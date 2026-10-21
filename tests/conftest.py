import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture()
def client(tmp_path):
    """Cliente con una BD SQLite temporal por test (aislamiento total de estado).

    Se sobreescribe DATABASE_URL antes del startup: el lifespan de la app crea
    el engine y el esquema exactamente igual que en producción (PostgreSQL),
    pero sobre un archivo temporal — mismos repositorios, servicios y rutas.
    """
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    get_settings.cache_clear()

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture()
def space(client):
    response = client.post(
        "/spaces",
        json={"spaceName": "Sala Norte", "type": "meeting_room", "capacity": 10, "description": "Sala con proyector"},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def company(client):
    response = client.post(
        "/companies",
        json={
            "companyName": "Empresa Uno",
            "rut": "12345678-5",
            "email": "contacto@empresa.cl",
            "phone": "12345678",
            "address": "Calle Principal 123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def make_reservation(client, space_id, company_id, start="2030-01-10T10:00:00", end="2030-01-10T12:00:00", **extra):
    payload = {
        "spaceId": space_id,
        "companyId": company_id,
        "start_date": start,
        "end_date": end,
        "reason": "Reunion de equipo",
        **extra,
    }
    return client.post("/reservations", json=payload)
