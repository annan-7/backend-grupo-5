from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.core.base_schema import ApiModel
from app.domain.reservation import MIN_DURATION_MINUTES, ReservationStatus
from app.domain.validators import ensure_utc


class ReservationBase(ApiModel):
    space_id: str = Field(min_length=1, description="Space ID (must exist)")
    company_id: str = Field(min_length=1, description="Company ID (must exist)")
    start_date: datetime
    end_date: datetime
    reason: str = Field(min_length=5, max_length=200)

    @field_validator("start_date", "end_date", mode="after")
    @classmethod
    def normalize_to_utc(cls, value: datetime) -> datetime:
        # Fechas naive se interpretan como UTC; fechas aware se convierten a UTC.
        # Evita el TypeError al comparar naive vs aware (bug 1.1 de la revisión).
        return ensure_utc(value)

    @model_validator(mode="after")
    def validate_schedule(self) -> "ReservationBase":
        if self.end_date <= self.start_date:
            raise ValueError("End date must be later than start date")
        duration_minutes = (self.end_date - self.start_date).total_seconds() / 60
        if duration_minutes < MIN_DURATION_MINUTES:
            raise ValueError(f"Minimum duration must be {MIN_DURATION_MINUTES} minutes")
        return self


class ReservationCreate(ReservationBase):
    # Sin campo `status`: toda reserva nace en PENDING. Los cambios de estado
    # pasan por la máquina de estados (PUT status, /confirm, /cancel, /complete).
    pass


class ReservationUpdate(ApiModel):
    space_id: str | None = Field(None, min_length=1)
    company_id: str | None = Field(None, min_length=1)
    start_date: datetime | None = None
    end_date: datetime | None = None
    reason: str | None = Field(None, min_length=5, max_length=200)
    status: ReservationStatus | None = None

    @field_validator("start_date", "end_date", mode="after")
    @classmethod
    def normalize_to_utc(cls, value: datetime | None) -> datetime | None:
        return ensure_utc(value) if value is not None else None


class ReservationResponse(ReservationBase):
    reservation_id: str
    status: ReservationStatus
    created_at: datetime
    updated_at: datetime
