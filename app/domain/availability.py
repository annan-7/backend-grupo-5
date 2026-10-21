from dataclasses import dataclass
from datetime import datetime, time
from enum import StrEnum

from app.core.exceptions import BusinessRuleError
from app.domain.validators import utc_now


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


@dataclass
class Availability:
    availability_id: str
    space_id: str
    weekday: Weekday
    opening_time: time
    closing_time: time
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        availability_id: str,
        space_id: str,
        weekday: Weekday,
        opening_time: time,
        closing_time: time,
    ) -> "Availability":
        if closing_time <= opening_time:
            raise BusinessRuleError("Closing time must be later than opening time")
        now = utc_now()
        return cls(
            availability_id=availability_id,
            space_id=space_id.strip(),
            weekday=weekday,
            opening_time=opening_time,
            closing_time=closing_time,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        space_id: str | None = None,
        weekday: Weekday | None = None,
        opening_time: time | None = None,
        closing_time: time | None = None,
    ) -> None:
        new_opening = self.opening_time if opening_time is None else opening_time
        new_closing = self.closing_time if closing_time is None else closing_time
        if new_closing <= new_opening:
            raise BusinessRuleError("Closing time must be later than opening time")
        if space_id is not None:
            self.space_id = space_id.strip()
        if weekday is not None:
            self.weekday = weekday
        self.opening_time = new_opening
        self.closing_time = new_closing
        self.updated_at = utc_now()

    def overlaps(self, opening_time: time, closing_time: time) -> bool:
        """True si el rango [opening, closing) se solapa con esta ventana."""
        return opening_time < self.closing_time and closing_time > self.opening_time

    def contains(self, opening_time: time, closing_time: time) -> bool:
        """True si el rango [opening, closing] cabe completamente en esta ventana."""
        return self.opening_time <= opening_time and closing_time <= self.closing_time
