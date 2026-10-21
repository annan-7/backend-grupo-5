from datetime import time as dtime
from datetime import timedelta
from uuid import uuid4

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.domain.reservation import Reservation
from app.domain.validators import ensure_utc
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.space_repository import SpaceRepository
from app.schemas.reservation import ReservationCreate, ReservationUpdate

_END_OF_DAY = dtime(23, 59, 59, 999999)
_START_OF_DAY = dtime(0, 0)

# Mapeo weekday de Python -> enum del dominio
_WEEKDAY_MAP = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


class ReservationService:
    def __init__(
        self,
        reservation_repository: ReservationRepository,
        space_repository: SpaceRepository,
        company_repository: CompanyRepository,
        availability_repository: AvailabilityRepository,
    ) -> None:
        self.reservation_repository = reservation_repository
        self.space_repository = space_repository
        self.company_repository = company_repository
        self.availability_repository = availability_repository

    # ------------------------------------------------------------------ CRUD

    async def create(self, data: ReservationCreate) -> Reservation:
        space = await self._ensure_space_exists(data.space_id)
        await self._ensure_company_exists(data.company_id)
        if not space.is_active:
            raise BusinessRuleError(
                f"Reservations can only be created for active spaces (space status: '{space.status.value}')"
            )
        start, end = ensure_utc(data.start_date), ensure_utc(data.end_date)
        await self._ensure_no_conflicts(data.space_id, data.company_id, start, end)
        await self._ensure_within_availability(data.space_id, start, end)
        reservation = Reservation.create(
            reservation_id=str(uuid4()),
            space_id=data.space_id,
            company_id=data.company_id,
            start_date=start,
            end_date=end,
            reason=data.reason,
        )
        return await self.reservation_repository.add(reservation)

    async def get_by_id(self, reservation_id: str) -> Reservation:
        reservation = await self.reservation_repository.get_by_id(reservation_id)
        if reservation is None:
            raise NotFoundError(f"Reservation '{reservation_id}' was not found")
        return reservation

    async def get_all(self) -> list[Reservation]:
        return await self.reservation_repository.get_all()

    async def update(self, reservation_id: str, data: ReservationUpdate) -> Reservation:
        reservation = await self.get_by_id(reservation_id)

        schedule_payload = data.model_dump(exclude_unset=True, exclude={"status", "reason"})
        schedule_changed = bool(schedule_payload)

        # Reservas terminales (canceled/completed) son inmutables salvo `reason`.
        if not reservation.is_active:
            if schedule_changed:
                raise BusinessRuleError(
                    f"Cannot modify schedule/space/company of a {reservation.status.value} reservation"
                )
            if data.reason is not None:
                reservation.set_reason(data.reason)
                await self.reservation_repository.update(reservation)
            if data.status is not None:
                reservation.transition_to(data.status)  # terminales: no hay transición legal
                await self.reservation_repository.update(reservation)
            return reservation

        if schedule_changed:
            space_id = data.space_id if data.space_id is not None else reservation.space_id
            company_id = data.company_id if data.company_id is not None else reservation.company_id
            start_date = ensure_utc(data.start_date) if data.start_date is not None else reservation.start_date
            end_date = ensure_utc(data.end_date) if data.end_date is not None else reservation.end_date

            space = await self._ensure_space_exists(space_id)
            if not space.is_active:
                raise BusinessRuleError(
                    f"Reservations can only use active spaces (space status: '{space.status.value}')"
                )
            await self._ensure_company_exists(company_id)
            if end_date <= start_date:
                raise BusinessRuleError("End date must be later than start date")
            if (end_date - start_date).total_seconds() < 30 * 60:
                raise BusinessRuleError("Minimum duration must be 30 minutes")
            await self._ensure_no_conflicts(
                space_id, company_id, start_date, end_date, exclude_reservation_id=reservation_id
            )
            await self._ensure_within_availability(space_id, start_date, end_date)
            reservation.reschedule(space_id, company_id, start_date, end_date)

        if data.reason is not None:
            reservation.set_reason(data.reason)
        if data.status is not None:
            # Máquina de estados del dominio: pending->confirmed/canceled,
            # confirmed->canceled/completed; canceled/completed terminales.
            reservation.transition_to(data.status)
        return await self.reservation_repository.update(reservation)

    async def delete(self, reservation_id: str) -> None:
        reservation = await self.get_by_id(reservation_id)
        await self.reservation_repository.delete(reservation)

    # ------------------------------------------------- transiciones explícitas

    async def confirm(self, reservation_id: str) -> Reservation:
        reservation = await self.get_by_id(reservation_id)
        reservation.confirm()
        return await self.reservation_repository.update(reservation)

    async def cancel(self, reservation_id: str) -> Reservation:
        reservation = await self.get_by_id(reservation_id)
        reservation.cancel()
        return await self.reservation_repository.update(reservation)

    async def complete(self, reservation_id: str) -> Reservation:
        reservation = await self.get_by_id(reservation_id)
        reservation.complete()
        return await self.reservation_repository.update(reservation)

    # ------------------------------------------------------------- validaciones

    async def _ensure_space_exists(self, space_id: str):
        space = await self.space_repository.get_by_id(space_id)
        if space is None:
            raise NotFoundError(f"Space '{space_id}' was not found")
        return space

    async def _ensure_company_exists(self, company_id: str) -> None:
        if await self.company_repository.get_by_id(company_id) is None:
            raise NotFoundError(f"Company '{company_id}' was not found")

    async def _ensure_no_conflicts(
        self,
        space_id: str,
        company_id: str,
        start_date,
        end_date,
        exclude_reservation_id: str | None = None,
    ) -> None:
        """RN2 (sin solape en el mismo espacio) y RN3 (empresa sin reservas simultáneas)."""
        conflicts = await self.reservation_repository.find_active_conflicts(
            space_id, company_id, start_date, end_date, exclude_reservation_id
        )
        for reservation in conflicts:
            if reservation.space_id == space_id:
                raise ConflictError("The space is already reserved for the requested period")
            if reservation.company_id == company_id:
                raise ConflictError("The company already has a reservation for the requested period")

    async def _ensure_within_availability(self, space_id: str, start_date, end_date) -> None:
        """RN5: la reserva debe caber en las ventanas de disponibilidad del espacio.

        Política: para cada día que atraviesa la reserva, si el espacio tiene
        ventanas definidas para ese día de la semana, el tramo de ese día debe
        caber completo en UNA de ellas. Días sin ventanas cargadas no tienen
        restricción horaria.
        """
        windows = await self.availability_repository.get_by_space(space_id)
        if not windows:
            return
        windows_by_weekday: dict[str, list] = {}
        for window in windows:
            windows_by_weekday.setdefault(window.weekday.value, []).append(window)

        current_day = start_date.date()
        last_day = end_date.date()
        while current_day <= last_day:
            weekday_name = _WEEKDAY_MAP[current_day.weekday()]
            day_windows = windows_by_weekday.get(weekday_name)
            if day_windows:
                segment_start = start_date.time() if current_day == start_date.date() else _START_OF_DAY
                segment_end = end_date.time() if current_day == last_day else _END_OF_DAY
                if segment_start < segment_end and not any(w.contains(segment_start, segment_end) for w in day_windows):
                    allowed = ", ".join(f"{w.opening_time:%H:%M}-{w.closing_time:%H:%M}" for w in day_windows)
                    raise BusinessRuleError(
                        f"Reservation is outside the availability window for {weekday_name} "
                        f"({segment_start:%H:%M}-{segment_end:%H:%M} does not fit in: {allowed})"
                    )
            current_day = current_day + timedelta(days=1)
