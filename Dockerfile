# syntax=docker/dockerfile:1
# ============================================================
# Coworking Reservation API — Backend 2026, Grupo 05
# Imagen de producción: multi-stage, sin herramientas de build,
# usuario no-root y healthcheck sobre GET /.
#
#   docker build -t coworking-api .
#   docker run --rm -p 8000:8000 coworking-api
# ============================================================

# ---------- Etapa 1: dependencias (venv aislado con uv) ----------
FROM python:3.11-slim AS builder

# Binario de uv desde la imagen oficial (se descarta en la etapa final)
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Solo los manifiestos primero: esta capa se reutiliza mientras
# pyproject.toml/uv.lock no cambien (cacheo eficiente de dependencias).
COPY pyproject.toml uv.lock ./

# --frozen: respeta uv.lock sin re-resolver (builds reproducibles)
# --no-dev: excluye pytest/ruff de la imagen de producción
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- Etapa 2: imagen final ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Usuario no-root dedicado
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --create-home appuser

# venv pre-construido + código de la aplicación
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --chown=appuser:appgroup app ./app

USER appuser
EXPOSE 8000

# Healthcheck sin dependencias extra (usa urllib de la stdlib contra GET /)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/').status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
