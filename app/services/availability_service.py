from uuid import uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.availability import Availability, Weekday
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.space_repository import SpaceRepository
from app.schemas.availability import AvailabilityCreate, AvailabilityUpdate


class AvailabilityService:
    def __init__(self, availability_repository: AvailabilityRepository, space_repository: SpaceRepository) -> None:
        self.availability_repository = availability_repository
        self.space_repository = space_repository

    async def create(self, data: AvailabilityCreate) -> Availability:
        await self._ensure_space_exists(data.space_id)
        await self._ensure_no_overlap(
            space_id=data.space_id,
            weekday=data.weekday,
            opening_time=data.opening_time,
            closing_time=data.closing_time,
        )
        availability = Availability.create(
            availability_id=str(uuid4()),
            space_id=data.space_id,
            weekday=data.weekday,
            opening_time=data.opening_time,
            closing_time=data.closing_time,
        )
        return await self.availability_repository.add(availability)

    async def get_by_id(self, availability_id: str) -> Availability:
        availability = await self.availability_repository.get_by_id(availability_id)
        if availability is None:
            raise NotFoundError(f"Availability '{availability_id}' was not found")
        return availability

    async def get_all(self) -> list[Availability]:
        return await self.availability_repository.get_all()

    async def update(self, availability_id: str, data: AvailabilityUpdate) -> Availability:
        availability = await self.get_by_id(availability_id)
        space_id = data.space_id if data.space_id is not None else availability.space_id
        weekday = data.weekday if data.weekday is not None else availability.weekday
        opening_time = data.opening_time if data.opening_time is not None else availability.opening_time
        closing_time = data.closing_time if data.closing_time is not None else availability.closing_time
        if data.space_id is not None:
            await self._ensure_space_exists(data.space_id)
        await self._ensure_no_overlap(
            space_id=space_id,
            weekday=weekday,
            opening_time=opening_time,
            closing_time=closing_time,
            exclude_availability_id=availability_id,
        )
        availability.update(
            space_id=data.space_id,
            weekday=data.weekday,
            opening_time=data.opening_time,
            closing_time=data.closing_time,
        )
        return await self.availability_repository.update(availability)

    async def delete(self, availability_id: str) -> None:
        availability = await self.get_by_id(availability_id)
        await self.availability_repository.delete(availability)

    async def _ensure_space_exists(self, space_id: str) -> None:
        if await self.space_repository.get_by_id(space_id) is None:
            raise NotFoundError(f"Space '{space_id}' was not found")

    async def _ensure_no_overlap(
        self,
        space_id: str,
        weekday: Weekday,
        opening_time,
        closing_time,
        exclude_availability_id: str | None = None,
    ) -> None:
        """Prohíbe ventanas horarias solapadas para el mismo espacio+día."""
        overlapping = await self.availability_repository.find_overlapping(
            space_id, weekday, opening_time, closing_time, exclude_availability_id
        )
        if overlapping:
            other = overlapping[0]
            raise ConflictError(
                f"Space '{space_id}' already has an availability window on {weekday.value} "
                f"({other.opening_time:%H:%M}-{other.closing_time:%H:%M}) that overlaps "
                f"{opening_time:%H:%M}-{closing_time:%H:%M}"
            )
