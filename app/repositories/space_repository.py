from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SpaceORM
from app.db.session import parse_uuid
from app.domain.space import Space, SpaceStatus, SpaceType
from app.domain.validators import ensure_utc


def to_domain(row: SpaceORM) -> Space:
    return Space(
        space_id=str(row.id),
        space_name=row.space_name,
        type=SpaceType(row.type),
        capacity=row.capacity,
        status=SpaceStatus(row.status),
        description=row.description,
        created_at=ensure_utc(row.created_at),
        updated_at=ensure_utc(row.updated_at),
    )


def to_orm(space: Space) -> SpaceORM:
    return SpaceORM(
        id=parse_uuid(space.space_id),
        space_name=space.space_name,
        type=space.type.value,
        capacity=space.capacity,
        status=space.status.value,
        description=space.description,
        created_at=space.created_at,
        updated_at=space.updated_at,
    )


class SpaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, space: Space) -> Space:
        self.session.add(to_orm(space))
        await self.session.flush()
        return space

    async def get_by_id(self, space_id: str) -> Space | None:
        pk = parse_uuid(space_id)
        if pk is None:
            return None
        row = await self.session.get(SpaceORM, pk)
        return to_domain(row) if row is not None else None

    async def get_all(self) -> list[Space]:
        rows = (await self.session.execute(select(SpaceORM))).scalars().all()
        return [to_domain(row) for row in rows]

    async def update(self, space: Space) -> Space:
        row = await self.session.get(SpaceORM, parse_uuid(space.space_id))
        if row is not None:
            row.space_name = space.space_name
            row.type = space.type.value
            row.capacity = space.capacity
            row.status = space.status.value
            row.description = space.description
            row.updated_at = space.updated_at
            await self.session.flush()
        return space

    async def delete(self, space: Space) -> None:
        row = await self.session.get(SpaceORM, parse_uuid(space.space_id))
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()
