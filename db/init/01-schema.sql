-- ============================================================
-- 01-schema.sql — Esquema de la Coworking Reservation API
--
-- Refleja EXACTAMENTE los modelos SQLAlchemy de app/db/models.py
-- (mismos nombres de tablas, columnas, tipos, constraints e índices).
-- La app ejecuta Base.metadata.create_all al arrancar, que es
-- idempotente: si estas tablas ya existen, no las toca ni duplica.
--
-- Se ejecuta automáticamente la primera vez que se inicia el
-- contenedor (volumen vacío), vía /docker-entrypoint-initdb.d/.
-- ============================================================

CREATE TABLE IF NOT EXISTS spaces (
    id          UUID PRIMARY KEY,
    space_name  VARCHAR(50)  NOT NULL,
    type        VARCHAR(30)  NOT NULL,
    capacity    INTEGER      NOT NULL,
    status      VARCHAR(20)  NOT NULL,
    description VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL,
    updated_at  TIMESTAMPTZ  NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_spaces_type   ON spaces (type);
CREATE INDEX IF NOT EXISTS ix_spaces_status ON spaces (status);

CREATE TABLE IF NOT EXISTS companies (
    id           UUID PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    rut          VARCHAR(12)  NOT NULL UNIQUE,
    email        VARCHAR(254) NOT NULL UNIQUE,
    phone        VARCHAR(15)  NOT NULL,
    address      VARCHAR(100) NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL,
    updated_at   TIMESTAMPTZ  NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_companies_rut   ON companies (rut);
CREATE INDEX IF NOT EXISTS ix_companies_email ON companies (email);

CREATE TABLE IF NOT EXISTS reservations (
    id           UUID PRIMARY KEY,
    space_id     UUID        NOT NULL REFERENCES spaces (id)   ON DELETE RESTRICT,
    company_id   UUID        NOT NULL REFERENCES companies (id) ON DELETE RESTRICT,
    start_date   TIMESTAMPTZ NOT NULL,
    end_date     TIMESTAMPTZ NOT NULL,
    status       VARCHAR(20) NOT NULL,
    reason       VARCHAR(200) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_reservations_space_id   ON reservations (space_id);
CREATE INDEX IF NOT EXISTS ix_reservations_company_id ON reservations (company_id);
CREATE INDEX IF NOT EXISTS ix_reservations_start_date ON reservations (start_date);
CREATE INDEX IF NOT EXISTS ix_reservations_status     ON reservations (status);

CREATE TABLE IF NOT EXISTS availabilities (
    id           UUID PRIMARY KEY,
    space_id     UUID        NOT NULL REFERENCES spaces (id) ON DELETE CASCADE,
    weekday      VARCHAR(12) NOT NULL,
    opening_time TIME        NOT NULL,
    closing_time TIME        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_availabilities_space_id ON availabilities (space_id);
CREATE INDEX IF NOT EXISTS ix_availabilities_weekday  ON availabilities (weekday);
