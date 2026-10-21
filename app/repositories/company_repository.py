from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CompanyORM
from app.db.session import parse_uuid
from app.domain.company import Company
from app.domain.validators import ensure_utc


def to_domain(row: CompanyORM) -> Company:
    return Company(
        company_id=str(row.id),
        company_name=row.company_name,
        rut=row.rut,
        email=row.email,
        phone=row.phone,
        address=row.address,
        created_at=ensure_utc(row.created_at),
        updated_at=ensure_utc(row.updated_at),
    )


def to_orm(company: Company) -> CompanyORM:
    return CompanyORM(
        id=parse_uuid(company.company_id),
        company_name=company.company_name,
        rut=company.rut,
        email=company.email,
        phone=company.phone,
        address=company.address,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, company: Company) -> Company:
        self.session.add(to_orm(company))
        await self.session.flush()
        return company

    async def get_by_id(self, company_id: str) -> Company | None:
        pk = parse_uuid(company_id)
        if pk is None:
            return None
        row = await self.session.get(CompanyORM, pk)
        return to_domain(row) if row is not None else None

    async def get_all(self) -> list[Company]:
        rows = (await self.session.execute(select(CompanyORM))).scalars().all()
        return [to_domain(row) for row in rows]

    async def find_by_rut(self, rut: str, exclude_company_id: str | None = None) -> Company | None:
        stmt = select(CompanyORM).where(CompanyORM.rut == rut)
        exclude = parse_uuid(exclude_company_id) if exclude_company_id else None
        if exclude is not None:
            stmt = stmt.where(CompanyORM.id != exclude)
        row = (await self.session.execute(stmt.limit(1))).scalar_one_or_none()
        return to_domain(row) if row is not None else None

    async def find_by_email(self, email: str, exclude_company_id: str | None = None) -> Company | None:
        stmt = select(CompanyORM).where(CompanyORM.email == email)
        exclude = parse_uuid(exclude_company_id) if exclude_company_id else None
        if exclude is not None:
            stmt = stmt.where(CompanyORM.id != exclude)
        row = (await self.session.execute(stmt.limit(1))).scalar_one_or_none()
        return to_domain(row) if row is not None else None

    async def update(self, company: Company) -> Company:
        row = await self.session.get(CompanyORM, parse_uuid(company.company_id))
        if row is not None:
            row.company_name = company.company_name
            row.rut = company.rut
            row.email = company.email
            row.phone = company.phone
            row.address = company.address
            row.updated_at = company.updated_at
            await self.session.flush()
        return company

    async def delete(self, company: Company) -> None:
        row = await self.session.get(CompanyORM, parse_uuid(company.company_id))
        if row is not None:
            await self.session.delete(row)
            await self.session.flush()
