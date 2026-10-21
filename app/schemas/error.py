from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []


class ErrorResponse(BaseModel):
    """Enveloppe de error estándar de la API (todos los códigos 4xx/5xx)."""

    error: ErrorPayload
