"""Excepciones de aplicación.

Todas heredan de ``ApiError`` y son convertidas a la enveloppe JSON estándar
``{"error": {code, message, details}}`` por el manejador global registrado en
``app/main.py``. Los routers NO deben capturarlas: se propagan desde servicios
y dominio hasta el handler central (único punto de mapeo error -> HTTP).
"""

from typing import Any


class ApiError(Exception):
    """Error controlado de la aplicación."""

    status_code: int = 400
    code: str = "ERROR"

    def __init__(self, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        self.message = message
        self.details: list[dict[str, Any]] = details or []
        super().__init__(message)


class BusinessRuleError(ApiError):
    """Violación de una regla de negocio (HTTP 400)."""

    status_code = 400
    code = "BUSINESS_RULE_VIOLATION"


class NotFoundError(ApiError):
    """Recurso inexistente (HTTP 404)."""

    status_code = 404
    code = "RESOURCE_NOT_FOUND"


class ConflictError(ApiError):
    """Conflicto con el estado actual del recurso (HTTP 409)."""

    status_code = 409
    code = "CONFLICT"
