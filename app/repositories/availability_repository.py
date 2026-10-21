from datetime import time as dt_time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AvailabilityORM
from app.db.session import parse_uuid
from app.domain.availability import Availability, Weekday
from app.domain.validators import ensure_utc


def to_domain(row: AvailabilityORM) -> Availability:
    return Availability(
        availability_id=str(row.id),
        space_id=str(row.space_id),
        weekday=Weekday(row.weekday),
        opening_time=row.opening_time,
        closing_time=row.closing_time,
        created_at=ensure_utc(row.created_at),
        updated_at=ensure_utc(row.updated_at),
    )


def to_orm(availability: Availability) -> AvailabilityORM:
    return AvailabilityORM(
        id=parse_uuid(availability.availability_id),
        space_id=parse_uuid(availability.space_id),
        weekday=availability.weekday.value,
        opening_time=availability.opening_time,
        closing_time=availability.closing_time,
        created_at=availability.created_at,
        updated_at=availability.updated_at,
    )


class AvailabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, availability: Availability) -> Availability:
        self.session.add(to_orm(availability))
        await self.session.flush()
        return availability

    async def get_by_id(self, availability_id: str) -> Availability | None:
        pk = parse_uuid(availability_id)
        if pk is None:
            return None
        row = await self.session.get(AvailabilityORM, pk)
        return to_domain(row) if row is not None else None

    async def get_all(self) -> list[Availability]:
        rows = (await self.session.execute(select(AvailabilityORM))).scalars().all()
        return [to_domain(row) for row in rows]

    async def get_by_space(self, space_id: str) -> list[Availability]:
        space_pk = parse_uuid(space_id)
        if space_pk is None:
            return []
        stmt = select(AvailabilityORM).where(AvailabilityORM.space_id == space_pk)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(row) for row in rows]

    async def find_overlapping(
        self,
        space_id: str,
        weekday: Weekday,
        opening_time: dt_time,
        closing_time: dt_time,
        exclude_availability_id: str | None = None,
    ) -> list[Availability]:
        """Ventanas del mismo espacio+día que se solapan con [opening, closing)."""
        space_pk = parse_uuid(space_id)
        if space_pk is None:
            return []
        stmt = select(AvailabilityORM).where(
            AvailabilityORM.space_id == space_pk,
            AvailabilityORM.weekday == weekday.value,
            AvailabilityORM.opening_time < closing_time,
            AvailabilityORM.closing_time > opening_time,
        )
        if exclude_availability_id is not None:
            exclude_pk = parse_uuid(exclude_availability_id)
            if exclude_pk is not None:
                stmt = stmt.where(AvailabilityORM.id != exclude_pk)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [to_domain(row) for row in rows]

    async def update(self, availability: Availability) -> Availability:
        row = await self.session.get(AvailabilityORM, parse_uuid(availability.availability_id))
        if row is not None:
            row.space_id = parse_uuid(availability.space_id)
            row.weekday = availability.weekday.value
            row.opening_time = availability.opening_time
            row.closing_time = availability.closing_time
            row.updated_at = availability.updated_at
            await self.session.flush()
        return availability

    async def delete(self, availability: Availability) -> None:
        row = await self.session.get(AvailabilityORM, parse_uuid(availability.availability_id))
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()

    async def delete_by_space(self, space_id: str) -> int:
        space_pk = parse_uuid(space_id)
        if space_pk is None:
            return 0
        result = await self.session.execute(delete(AvailabilityORM).where(AvailabilityORM.space_id == space_pk))
        await self.session.flush()
        return result.rowcount or 0
