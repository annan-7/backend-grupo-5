"""Modelos ORM (tablas SQL).

Convenciones:
- PKs ``Uuid``: nativo en PostgreSQL, portable a SQLite (CHAR(32)) para tests.
- Enums del dominio persistidos como ``String`` con su ``.value`` (portable y
  sin tipos ENUM nativos que compliquen migraciones).
- ``DateTime(timezone=True)``: timestamptz en PostgreSQL; en SQLite se guarda
  UTC naive y el mapeo de vuelta al dominio aplica ``ensure_utc``.
- El dominio sigue siendo puro (dataclasses): los repositorios mapean
  ORM <-> dominio y los servicios nunca tocan objetos ORM.
"""

from datetime import datetime
from datetime import time as dt_time
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Time, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SpaceORM(Base):
    __tablename__ = "spaces"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    space_name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(30), index=True)
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CompanyORM(Base):
    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(100))
    # Unicidad garantizada por la BD (backstop a prueba de carreras),
    # además del chequeo amigable en el servicio.
    rut: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(15))
    address: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReservationORM(Base):
    __tablename__ = "reservations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    space_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("spaces.id", ondelete="RESTRICT"), index=True)
    company_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), index=True)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AvailabilityORM(Base):
    __tablename__ = "availabilities"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    space_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("spaces.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[str] = mapped_column(String(12), index=True)
    opening_time: Mapped[dt_time] = mapped_column(Time)
    closing_time: Mapped[dt_time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
