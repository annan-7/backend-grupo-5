from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReservationORM
from app.db.session import parse_uuid
from app.domain.reservation import ACTIVE_STATUSES, Reservation, ReservationStatus
from app.domain.validators import ensure_utc

_ACTIVE_VALUES = [status.value for status in ACTIVE_STATUSES]


def to_domain(row: ReservationORM) -> Reservation:
    return Reservation(
        reservation_id=str(row.id),
        space_id=str(row.space_id),
        company_id=str(row.company_id),
        start_date=ensure_utc(row.start_date),
        end_date=ensure_utc(row.end_date),
        status=ReservationStatus(row.status),
        reason=row.reason,
        created_at=ensure_utc(row.created_at),
        updated_at=ensure_utc(row.updated_at),
    )


def to_orm(reservation: Reservation) -> ReservationORM:
    return ReservationORM(
        id=parse_uuid(reservation.reservation_id),
        space_id=parse_uuid(reservation.space_id),
        company_id=parse_uuid(reservation.company_id),
        start_date=reservation.start_date,
        end_date=reservation.end_date,
        status=reservation.status.value,
        reason=reservation.reason,
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
    )


class ReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, reservation: Reservation) -> Reservation:
        self.session.add(to_orm(reservation))
        await self.session.flush()
        return reservation

    async def get_by_id(self, reservation_id: str) -> Reservation | None:
        pk = parse_uuid(reservation_id)
        if pk is None:
            return None
        row = await self.session.get(ReservationORM, pk)
        return to_domain(row) if row is not None else None

    async def get_all(self) -> list[Reservation]:
        rows = (await self.session.execute(select(ReservationORM))).scalars().all()
        return [to_domain(row) for row in rows]

    async def find_active_conflicts(
        self,
        space_id: str,
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        exclude_reservation_id: str | None = None,
    ) -> list[Reservation]:
        """Reservas activas que se solapan con el rango pedido, en el mismo
        espacio O para la misma empresa (RN2/RN3 resueltas en SQL)."""
        space_pk, company_pk = parse_uuid(space_id), parse_uuid(company_id)
        if space_pk is None or company_pk is None:
            return []
        stmt = select(ReservationORM).where(
            ReservationORM.status.in_(_ACTIVE_VALUES),
            ReservationORM.start_date < end_date,
            ReservationORM.end_date > start_date,
            or_(ReservationORM.space_id == space_pk, ReservationORM.company_id == company_pk),
        )
        if exclude_reservation_id is not None:
            exclude_pk = parse_uuid(exclude_reservation_id)
            if exclude_pk is not None:
                stmt = stmt.where(ReservationORM.id != exclude_pk)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(row) for row in rows]

    async def find_active_by_space(self, space_id: str, end_after: datetime | None = None) -> list[Reservation]:
        """Reservas activas (pending/confirmed) de un espacio.

        Si se entrega ``end_after``, solo las que terminan después de ese instante.
        """
        space_pk = parse_uuid(space_id)
        if space_pk is None:
            return []
        stmt = select(ReservationORM).where(
            ReservationORM.space_id == space_pk,
            ReservationORM.status.in_(_ACTIVE_VALUES),
        )
        if end_after is not None:
            stmt = stmt.where(ReservationORM.end_date > end_after)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(row) for row in rows]

    async def find_active_by_company(self, company_id: str) -> list[Reservation]:
        company_pk = parse_uuid(company_id)
        if company_pk is None:
            return []
        stmt = select(ReservationORM).where(
            ReservationORM.company_id == company_pk,
            ReservationORM.status.in_(_ACTIVE_VALUES),
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(row) for row in rows]

    async def update(self, reservation: Reservation) -> Reservation:
        row = await self.session.get(ReservationORM, parse_uuid(reservation.reservation_id))
        if row is not None:
            row.space_id = parse_uuid(reservation.space_id)
            row.company_id = parse_uuid(reservation.company_id)
            row.start_date = reservation.start_date
            row.end_date = reservation.end_date
            row.status = reservation.status.value
            row.reason = reservation.reason
            row.updated_at = reservation.updated_at
            await self.session.flush()
        return reservation

    async def delete(self, reservation: Reservation) -> None:
        row = await self.session.get(ReservationORM, parse_uuid(reservation.reservation_id))
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()
