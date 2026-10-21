from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.core.exceptions import BusinessRuleError
from app.domain.validators import ensure_utc, utc_now, validate_text

MIN_DURATION_MINUTES = 30


class ReservationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    COMPLETED = "completed"


#: Estados que "ocupan" agenda (participan en chequeos de conflicto).
ACTIVE_STATUSES = frozenset({ReservationStatus.PENDING, ReservationStatus.CONFIRMED})

#: Máquina de estados: transiciones legales. CANCELED y COMPLETED son terminales.
ALLOWED_TRANSITIONS: dict[ReservationStatus, frozenset[ReservationStatus]] = {
    ReservationStatus.PENDING: frozenset({ReservationStatus.CONFIRMED, ReservationStatus.CANCELED}),
    ReservationStatus.CONFIRMED: frozenset({ReservationStatus.CANCELED, ReservationStatus.COMPLETED}),
    ReservationStatus.CANCELED: frozenset(),
    ReservationStatus.COMPLETED: frozenset(),
}

# Valida que la fecha de inicio sea anterior a la fecha de fin y que la duración mínima sea de 30 minutos.

def validate_schedule(start_date: datetime, end_date: datetime) -> tuple[datetime, datetime]:
    
    #Normaliza a UTC y valida orden y duración mínima (30 min).
    
    start = ensure_utc(start_date)
    end = ensure_utc(end_date)
    if end <= start:
        raise BusinessRuleError("End date must be later than start date")
    if (end - start).total_seconds() < MIN_DURATION_MINUTES * 60:
        raise BusinessRuleError(f"Minimum duration must be {MIN_DURATION_MINUTES} minutes")
    return start, end


@dataclass
class Reservation:
    reservation_id: str
    space_id: str
    company_id: str
    start_date: datetime
    end_date: datetime
    status: ReservationStatus
    reason: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        reservation_id: str,
        space_id: str,
        company_id: str,
        start_date: datetime,
        end_date: datetime,
        reason: str,
    ) -> "Reservation":
        start, end = validate_schedule(start_date, end_date)
        now = utc_now()
        return cls(
            reservation_id=reservation_id,
            space_id=space_id.strip(),
            company_id=company_id.strip(),
            start_date=start,
            end_date=end,
            status=ReservationStatus.PENDING,
            reason=validate_text(reason, "reason"),
            created_at=now,
            updated_at=now,
        )

    @property
    def is_active(self) -> bool:
        
        # Una reserva activa (pending/confirmed) ocupa agenda
        return self.status in ACTIVE_STATUSES

    def transition_to(self, new_status: ReservationStatus) -> None:
        #Cambia el estado validando la transición contra la máquina de estados.
        if new_status == self.status:
            return
        allowed = ALLOWED_TRANSITIONS[self.status]
        if new_status not in allowed:
            legal = ", ".join(sorted(s.value for s in allowed)) or "none (terminal state)"
            raise BusinessRuleError(
                f"Cannot change reservation status from '{self.status.value}' to '{new_status.value}'. "
                f"Legal transitions: {legal}"
            )
        self.status = new_status
        self.updated_at = utc_now()

    def confirm(self) -> None:
        self.transition_to(ReservationStatus.CONFIRMED)

    def cancel(self) -> None:
        self.transition_to(ReservationStatus.CANCELED)

    def complete(self) -> None:
        self.transition_to(ReservationStatus.COMPLETED)

    def reschedule(self, space_id: str, company_id: str, start_date: datetime, end_date: datetime) -> None:
        # Reagenda la reserva (solo permitido en reservas activas; lo controla el servicio).
        self.start_date, self.end_date = validate_schedule(start_date, end_date)
        self.space_id = space_id.strip()
        self.company_id = company_id.strip()
        self.updated_at = utc_now()

    def set_reason(self, reason: str) -> None:
        self.reason = validate_text(reason, "reason")
        self.updated_at = utc_now()
