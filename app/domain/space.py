from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.core.exceptions import BusinessRuleError
from app.domain.validators import utc_now, validate_text


class SpaceType(StrEnum):
    MEETING_ROOM = "meeting_room"
    PRIVATE_OFFICE = "private_office"
    OPEN_SPACE = "open_space"
    EVENT_SPACE = "event_space"


class SpaceStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


@dataclass
class Space:
    space_id: str
    space_name: str
    type: SpaceType
    capacity: int
    status: SpaceStatus
    description: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        space_id: str,
        space_name: str,
        type: SpaceType,
        capacity: int,
        description: str,
        status: SpaceStatus = SpaceStatus.ACTIVE,
    ) -> "Space":
        if capacity <= 0:
            raise BusinessRuleError("Capacity must be greater than zero")
        now = utc_now()
        return cls(
            space_id=space_id,
            space_name=validate_text(space_name, "space name"),
            type=type,
            capacity=capacity,
            status=status,
            description=validate_text(description, "description"),
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        space_name: str | None = None,
        type: SpaceType | None = None,
        capacity: int | None = None,
        status: SpaceStatus | None = None,
        description: str | None = None,
    ) -> None:
        if space_name is not None:
            self.space_name = validate_text(space_name, "space name")
        if type is not None:
            self.type = type
        if capacity is not None:
            if capacity <= 0:
                raise BusinessRuleError("Capacity must be greater than zero")
            self.capacity = capacity
        if status is not None:
            self.status = status
        if description is not None:
            self.description = validate_text(description, "description")
        self.updated_at = utc_now()

    @property
    def is_active(self) -> bool:
        return self.status == SpaceStatus.ACTIVE
