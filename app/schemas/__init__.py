"""DTOs Pydantic de la API (Create / Update / Response / filtros)."""

from app.schemas.availability import AvailabilityCreate, AvailabilityResponse, AvailabilityUpdate
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.schemas.error import ErrorDetail, ErrorPayload, ErrorResponse
from app.schemas.filter import (
    AvailabilityFilter,
    AvailabilityListQuery,
    CompanyFilter,
    CompanyListQuery,
    ReservationFilter,
    ReservationListQuery,
    SpaceFilter,
    SpaceListQuery,
)
from app.schemas.pagination import Paginated, Pagination
from app.schemas.reservation import ReservationCreate, ReservationResponse, ReservationUpdate
from app.schemas.space import SpaceCreate, SpaceResponse, SpaceUpdate

__all__ = [
    "AvailabilityCreate",
    "AvailabilityFilter",
    "AvailabilityListQuery",
    "AvailabilityResponse",
    "AvailabilityUpdate",
    "CompanyCreate",
    "CompanyFilter",
    "CompanyListQuery",
    "CompanyResponse",
    "CompanyUpdate",
    "ErrorDetail",
    "ErrorPayload",
    "ErrorResponse",
    "Paginated",
    "Pagination",
    "ReservationCreate",
    "ReservationFilter",
    "ReservationListQuery",
    "ReservationResponse",
    "ReservationUpdate",
    "SpaceCreate",
    "SpaceFilter",
    "SpaceListQuery",
    "SpaceResponse",
    "SpaceUpdate",
]
