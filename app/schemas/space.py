from datetime import datetime

from pydantic import Field

from app.core.base_schema import ApiModel
from app.domain.space import SpaceStatus, SpaceType


class SpaceBase(ApiModel):
    space_name: str = Field(min_length=3, max_length=50)
    type: SpaceType
    capacity: int = Field(ge=1, le=200, description="Capacity between 1 and 200")
    description: str = Field(min_length=1, max_length=200)


class SpaceCreate(SpaceBase):
    status: SpaceStatus = SpaceStatus.ACTIVE


class SpaceUpdate(ApiModel):
    space_name: str | None = Field(None, min_length=3, max_length=50)
    type: SpaceType | None = None
    capacity: int | None = Field(None, ge=1, le=200)
    status: SpaceStatus | None = None
    description: str | None = Field(None, min_length=1, max_length=200)


class SpaceResponse(SpaceBase):
    space_id: str
    status: SpaceStatus
    created_at: datetime
    updated_at: datetime
