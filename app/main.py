"""Punto de entrada de la API + manejo GLOBAL de errores + ciclo de vida de la BD.

Contrato de error único: toda respuesta 4xx/5xx tiene la forma
``{"error": {"code": str, "message": str, "details": [...]}}``.

Los handlers se registran UNA sola vez aquí; routers y servicios no hacen
try/except ni mapeo de mensajes por string matching.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import ApiError
from app.db.models import Base
from app.routers import availabilities, companies, reservations, spaces


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea el engine y asegura el esquema al arrancar; libera recursos al cerrar.

    Nota: ``create_all`` es idempotente y suficiente para el alcance del curso.
    Para evolución del esquema en producción se recomienda Alembic (README).
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=settings.echo_sql, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.engine = engine
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    yield
    await engine.dispose()


app = FastAPI(
    title="Coworking Reservation API",
    version="1.2.0",
    description=(
        "API REST para la gestión de reservas de espacios de coworking "
        "(Backend 2026 — Grupo 05). Persistencia: PostgreSQL + SQLAlchemy async."
    ),
    lifespan=lifespan,
)
app.include_router(spaces.router)
app.include_router(companies.router)
app.include_router(reservations.router)
app.include_router(availabilities.router)


def _error_response(
    status_code: int, code: str, message: str, details: list | None = None, headers: dict | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or []}},
        headers=headers,
    )


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, error: ApiError) -> JSONResponse:
    """Handler global de errores de dominio/negocio (NotFoundError, ConflictError, BusinessRuleError)."""
    return _error_response(error.status_code, error.code, error.message, error.details)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, error: StarletteHTTPException) -> JSONResponse:
    """HTTPException (rutas inexistentes, 405, etc.) con la misma enveloppe. Conserva headers."""
    detail = error.detail
    if isinstance(detail, dict) and "code" in detail:
        payload = detail
    else:
        payload = {"code": "HTTP_ERROR", "message": str(detail), "details": []}
    return JSONResponse(status_code=error.status_code, content={"error": payload}, headers=error.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    """422 de Pydantic (body y query params) con la misma enveloppe VALIDATION_ERROR."""
    details = []
    for item in error.errors():
        loc = [str(part) for part in item.get("loc", ()) if part not in ("body", "query", "path")]
        details.append({"field": ".".join(loc) or None, "message": item.get("msg", "Invalid value")})
    return _error_response(422, "VALIDATION_ERROR", "The request data is invalid", details)


@app.get("/", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok", "service": "Coworking Reservation API"}
