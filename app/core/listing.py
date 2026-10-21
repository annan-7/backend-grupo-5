"""Utilidad compartida por los routers para ordenar y paginar listados."""

from collections.abc import Sequence
from typing import Any

from app.schemas.pagination import Paginated


def build_page(items: Sequence[Any], page: int, limit: int, sort_by: str, direction: str) -> Paginated:
    """Ordena ``items`` por ``sort_by``/``direction`` y devuelve la página pedida.

    ``sort_by`` ya viene validado por un ``Literal`` en el esquema de query,
    así que ``getattr`` es seguro.
    """
    ordered = sorted(items, key=lambda item: getattr(item, sort_by), reverse=direction == "desc")
    total = len(ordered)
    start = (page - 1) * limit
    return Paginated(
        items=list(ordered[start : start + limit]),
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit,
    )
