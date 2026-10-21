from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.company import Company
from app.repositories.company_repository import CompanyRepository
from app.repositories.reservation_repository import ReservationRepository
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    def __init__(self, company_repository: CompanyRepository, reservation_repository: ReservationRepository) -> None:
        self.company_repository = company_repository
        self.reservation_repository = reservation_repository

    async def create(self, data: CompanyCreate) -> Company:
        rut = data.rut.strip().upper()
        email = str(data.email).strip().lower()
        await self._ensure_unique(rut=rut, email=email)
        company = Company.create(
            company_id=str(uuid4()),
            company_name=data.company_name,
            rut=rut,
            email=email,
            phone=data.phone,
            address=data.address,
        )
        try:
            return await self.company_repository.add(company)
        except IntegrityError as exc:
            # Backstop de los UNIQUE de la BD ante carreras entre requests.
            raise ConflictError(f"A company with RUT '{rut}' or email '{email}' already exists") from exc

    async def get_by_id(self, company_id: str) -> Company:
        company = await self.company_repository.get_by_id(company_id)
        if company is None:
            raise NotFoundError(f"Company '{company_id}' was not found")
        return company

    async def get_all(self) -> list[Company]:
        return await self.company_repository.get_all()

    async def update(self, company_id: str, data: CompanyUpdate) -> Company:
        company = await self.get_by_id(company_id)
        new_rut = data.rut.strip().upper() if data.rut is not None else None
        new_email = str(data.email).strip().lower() if data.email is not None else None
        await self._ensure_unique(rut=new_rut, email=new_email, exclude_company_id=company_id)
        company.update(
            company_name=data.company_name,
            rut=new_rut,
            email=new_email,
            phone=data.phone,
            address=data.address,
        )
        try:
            return await self.company_repository.update(company)
        except IntegrityError as exc:
            raise ConflictError("A company with that RUT or email already exists") from exc

    async def delete(self, company_id: str) -> None:
        company = await self.get_by_id(company_id)
        # Solo las reservas ACTIVAS bloquean el borrado (historial no).
        blocking = await self.reservation_repository.find_active_by_company(company_id)
        if blocking:
            raise ConflictError(f"Cannot delete company '{company_id}': it has {len(blocking)} active reservation(s)")
        await self.company_repository.delete(company)

    async def _ensure_unique(self, rut: str | None, email: str | None, exclude_company_id: str | None = None) -> None:
        """Unicidad de RUT y email (RN7): chequeo amigable antes del INSERT/UPDATE."""
        if rut is not None and await self.company_repository.find_by_rut(rut, exclude_company_id):
            raise ConflictError(f"A company with RUT '{rut}' already exists")
        if email is not None and await self.company_repository.find_by_email(email, exclude_company_id):
            raise ConflictError(f"A company with email '{email}' already exists")
