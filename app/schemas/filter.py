"""Filtros y modelos de query compuestos (paginación + filtro + orden).

Se usan con ``Annotated[XListQuery, Query()]``: FastAPI convierte cada campo
en un query param y valida solo (422 con enveloppe estándar si algo es inválido).
Reemplaza la validación manual que antes se hacía en los routers.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.domain.availability import Weekday
from app.domain.reservation import ReservationStatus
from app.domain.space import SpaceStatus, SpaceType
from app.schemas.pagination import Pagination


class SpaceFilter(BaseModel):
    type: SpaceType | None = Field(None, description="Filter by space type")
    status: SpaceStatus | None = Field(None, description="Filter by status")
    min_capacity: int | None = Field(None, ge=1, description="Minimum capacity")


class SpaceListQuery(Pagination, SpaceFilter):
    sort_by: Literal["space_name", "type", "capacity", "status", "created_at", "updated_at"] = "created_at"


class CompanyFilter(BaseModel):
    name: str | None = Field(None, min_length=1, description="Filter by company name (contains, case-insensitive)")
    rut: str | None = Field(None, description="Filter by exact RUT")


class CompanyListQuery(Pagination, CompanyFilter):
    sort_by: Literal["company_name", "rut", "email", "phone", "address", "created_at", "updated_at"] = "created_at"


class ReservationFilter(BaseModel):
    space_id: str | None = Field(None, description="Filter by space")
    company_id: str | None = Field(None, description="Filter by company")
    status: ReservationStatus | None = Field(None, description="Filter by reservation status")


class ReservationListQuery(Pagination, ReservationFilter):
    sort_by: Literal["start_date", "end_date", "status", "reason", "created_at", "updated_at"] = "created_at"


class AvailabilityFilter(BaseModel):
    space_id: str | None = Field(None, description="Filter by space")
    weekday: Weekday | None = Field(None, description="Filter by weekday")


class AvailabilityListQuery(Pagination, AvailabilityFilter):
    sort_by: Literal["weekday", "opening_time", "closing_time", "created_at", "updated_at"] = "created_at"
