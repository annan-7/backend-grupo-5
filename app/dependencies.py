"""Composición de la aplicación: sesión por request + fábricas de servicios.

Los routers obtienen los servicios con ``Depends(get_*_service)``; cada
fábrica recibe la ``AsyncSession`` del request y construye los repositorios.
En tests se sobreescribe ``get_session`` (o la variable DATABASE_URL).
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.space_repository import SpaceRepository
from app.services.availability_service import AvailabilityService
from app.services.company_service import CompanyService
from app.services.reservation_service import ReservationService
from app.services.space_service import SpaceService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_space_service(session: SessionDep) -> SpaceService:
    return SpaceService(
        SpaceRepository(session),
        ReservationRepository(session),
        AvailabilityRepository(session),
    )


def get_company_service(session: SessionDep) -> CompanyService:
    return CompanyService(CompanyRepository(session), ReservationRepository(session))


def get_reservation_service(session: SessionDep) -> ReservationService:
    return ReservationService(
        ReservationRepository(session),
        SpaceRepository(session),
        CompanyRepository(session),
        AvailabilityRepository(session),
    )


def get_availability_service(session: SessionDep) -> AvailabilityService:
    return AvailabilityService(AvailabilityRepository(session), SpaceRepository(session))
