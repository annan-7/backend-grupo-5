# syntax=docker/dockerfile:1
# ============================================================
# Imagen PostgreSQL personalizada — Coworking Reservation API
# Backend 2026, Grupo 05
#
# postgres:16-alpine + credenciales de desarrollo + scripts de
# inicialización (esquema + datos de demo) que corren SOLO la
# primera vez (volumen vacío), en orden alfabético:
#
#   /docker-entrypoint-initdb.d/01-schema.sql  -> tablas (idénticas al ORM)
#   /docker-entrypoint-initdb.d/02-seed.sql    -> datos de demostración
#
# Build directo:
#   docker build -t coworking-db ./db
#   docker run --rm -p 5432:5432 coworking-db
# ============================================================
FROM postgres:16-alpine

# Credenciales de desarrollo (sobreescribles con variables de entorno).
# Coinciden con el DATABASE_URL de desarrollo de la app y de docker-compose.
ENV POSTGRES_USER=proyecto \
    POSTGRES_PASSWORD='Bac"!k&E%n"#$d' \
    POSTGRES_DB=coworking \
    TZ=America/Santiago

# La app almacena todo en UTC (timestamptz); TZ solo afecta la
# visualización en psql.

COPY init/ /docker-entrypoint-initdb.d/

# Healthcheck a nivel de imagen: funciona también con `docker run` directo
# (docker-compose define el suyo, equivalente).
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
