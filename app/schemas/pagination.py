from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from app.core.base_schema import ApiModel

T = TypeVar("T")


class Pagination(BaseModel):
    """Parámetros comunes de paginación/orden (query params, nombres snake_case)."""

    page: int = Field(1, ge=1, description="Page number (starts at 1)")
    limit: int = Field(20, ge=1, le=100, description="Items per page (1 to 100)")
    direction: Literal["asc", "desc"] = Field("desc", description="Sort direction")


class Paginated(ApiModel, Generic[T]):
    """Enveloppe de respuesta para listados paginados."""

    items: list[T]
    total: int
    page: int
    limit: int
    total_pages: int
