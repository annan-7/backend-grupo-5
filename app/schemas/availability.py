from datetime import datetime, time

from pydantic import Field, model_validator

from app.core.base_schema import ApiModel
from app.domain.availability import Weekday


class AvailabilityBase(ApiModel):
    space_id: str = Field(min_length=1, description="Space ID (must exist)")
    weekday: Weekday
    opening_time: time
    closing_time: time

    @model_validator(mode="after")
    def validate_window(self) -> "AvailabilityBase":
        if self.closing_time <= self.opening_time:
            raise ValueError("Closing time must be later than opening time")
        return self


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityUpdate(ApiModel):
    space_id: str | None = Field(None, min_length=1)
    weekday: Weekday | None = None
    opening_time: time | None = None
    closing_time: time | None = None


class AvailabilityResponse(AvailabilityBase):
    availability_id: str
    created_at: datetime
    updated_at: datetime
