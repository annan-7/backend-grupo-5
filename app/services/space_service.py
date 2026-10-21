from uuid import uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.space import Space, SpaceStatus
from app.domain.validators import utc_now
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.space_repository import SpaceRepository
from app.schemas.space import SpaceCreate, SpaceUpdate


class SpaceService:
    def __init__(
        self,
        space_repository: SpaceRepository,
        reservation_repository: ReservationRepository,
        availability_repository: AvailabilityRepository,
    ) -> None:
        self.space_repository = space_repository
        self.reservation_repository = reservation_repository
        self.availability_repository = availability_repository

    async def create(self, data: SpaceCreate) -> Space:
        space = Space.create(
            space_id=str(uuid4()),
            space_name=data.space_name,
            type=data.type,
            capacity=data.capacity,
            description=data.description,
            status=data.status,
        )
        return await self.space_repository.add(space)

    async def get_by_id(self, space_id: str) -> Space:
        space = await self.space_repository.get_by_id(space_id)
        if space is None:
            raise NotFoundError(f"Space '{space_id}' was not found")
        return space

    async def get_all(self) -> list[Space]:
        return await self.space_repository.get_all()

    async def update(self, space_id: str, data: SpaceUpdate) -> Space:
        space = await self.get_by_id(space_id)
        # RN1 extendida: no se puede dejar un espacio no-activo si tiene
        # reservas futuras pendientes/confirmadas.
        if data.status is not None and data.status != SpaceStatus.ACTIVE:
            blocking = await self.reservation_repository.find_active_by_space(space_id, end_after=utc_now())
            if blocking:
                raise ConflictError(
                    f"Cannot change space '{space_id}' to '{data.status.value}': "
                    f"it has {len(blocking)} active upcoming reservation(s). "
                    "Cancel them first"
                )
        space.update(
            space_name=data.space_name,
            type=data.type,
            capacity=data.capacity,
            status=data.status,
            description=data.description,
        )
        return await self.space_repository.update(space)

    async def delete(self, space_id: str) -> None:
        space = await self.get_by_id(space_id)
        # Solo las reservas ACTIVAS bloquean el borrado; el historial no.
        blocking = await self.reservation_repository.find_active_by_space(space_id)
        if blocking:
            raise ConflictError(f"Cannot delete space '{space_id}': it has {len(blocking)} active reservation(s)")
        # Las disponibilidades son hijas del espacio: se eliminan en cascada.
        await self.availability_repository.delete_by_space(space_id)
        await self.space_repository.delete(space)
