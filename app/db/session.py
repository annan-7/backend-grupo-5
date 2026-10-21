"""Sesión SQLAlchemy por request = una transacción.

El commit se hace al terminar el request exitosamente; cualquier excepción
(incluidas las ``ApiError`` lanzadas por los servicios) provoca rollback.
Los servicios trabajan con objetos de dominio desvinculados de la sesión.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = request.app.state.sessionmaker
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def parse_uuid(value: str) -> UUID | None:
    """Convierte un id textual a UUID; devuelve None si no es un UUID válido.

    Permite que ids inválidos en la URL respondan 404 en vez de 500.
    """
    try:
        return UUID(value)
    except (ValueError, AttributeError, TypeError):
        return None
