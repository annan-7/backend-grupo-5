"""Modelos del dominio (dataclasses puros, sin dependencias de FastAPI)."""

from app.core.exceptions import ApiError, BusinessRuleError, ConflictError, NotFoundError
from app.domain.availability import Availability, Weekday
from app.domain.company import Company
from app.domain.reservation import (
    ACTIVE_STATUSES,
    ALLOWED_TRANSITIONS,
    Reservation,
    ReservationStatus,
)
from app.domain.space import Space, SpaceStatus, SpaceType
from app.domain.validators import validate_text

__all__ = [
    "ACTIVE_STATUSES",
    "ALLOWED_TRANSITIONS",
    "ApiError",
    "Availability",
    "BusinessRuleError",
    "Company",
    "ConflictError",
    "NotFoundError",
    "Reservation",
    "ReservationStatus",
    "Space",
    "SpaceStatus",
    "SpaceType",
    "Weekday",
    "validate_text",
]
