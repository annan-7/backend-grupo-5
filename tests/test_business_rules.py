"""Reglas de negocio del dominio (RN1-RN4) y validaciones de entrada."""

from tests.conftest import make_reservation


def test_rn1_cannot_reserve_inactive_space(client, space, company):
    client.put(f"/spaces/{space['spaceId']}", json={"status": "inactive"})
    response = make_reservation(client, space["spaceId"], company["companyId"])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_rn2_no_overlapping_reservations_same_space(client, space):
    company_a = client.post(
        "/companies",
        json={
            "companyName": "Empresa A",
            "rut": "11111111-1",
            "email": "a@x.cl",
            "phone": "11111111",
            "address": "Calle 1",
        },
    ).json()
    company_b = client.post(
        "/companies",
        json={
            "companyName": "Empresa B",
            "rut": "22222222-2",
            "email": "b@x.cl",
            "phone": "22222222",
            "address": "Calle 2",
        },
    ).json()
    assert make_reservation(client, space["spaceId"], company_a["companyId"]).status_code == 201
    overlap = make_reservation(
        client, space["spaceId"], company_b["companyId"], start="2030-01-10T11:00:00", end="2030-01-10T13:00:00"
    )
    assert overlap.status_code == 409
    # contigua (12:00 en adelante) no es conflicto
    contiguous = make_reservation(
        client, space["spaceId"], company_b["companyId"], start="2030-01-10T12:00:00", end="2030-01-10T13:00:00"
    )
    assert contiguous.status_code == 201


def test_rn3_company_cannot_have_simultaneous_reservations(client, space, company):
    other_space = client.post(
        "/spaces", json={"spaceName": "Sala Sur", "type": "open_space", "capacity": 5, "description": "d"}
    ).json()
    assert make_reservation(client, space["spaceId"], company["companyId"]).status_code == 201
    response = make_reservation(
        client, other_space["spaceId"], company["companyId"], start="2030-01-10T11:00:00", end="2030-01-10T12:30:00"
    )
    assert response.status_code == 409


def test_end_after_start_and_min_duration(client, space, company):
    response = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-10T12:00:00", end="2030-01-10T10:00:00"
    )
    assert response.status_code == 422  # validación de schema
    response = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-10T10:00:00", end="2030-01-10T10:29:00"
    )
    assert response.status_code == 422
    response = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-10T10:00:00", end="2030-01-10T10:30:00"
    )
    assert response.status_code == 201


def test_reservation_always_created_as_pending(client, space, company):
    """Bug 2.5: ya no se puede crear directamente en completed/canceled."""
    response = make_reservation(client, space["spaceId"], company["companyId"], status="completed")
    assert response.status_code == 201
    assert response.json()["status"] == "pending"  # el campo extra se ignora


def test_rut_modulo11_and_uniqueness(client):
    payload = {"companyName": "Empresa", "email": "x@y.cl", "phone": "12345678", "address": "Calle 123"}
    # DV incorrecto (el válido para 12345678 es 5)
    response = client.post("/companies", json={**payload, "rut": "12345678-0"})
    assert response.status_code == 400
    assert "verification digit" in response.json()["error"]["message"]
    # RUT válido
    assert client.post("/companies", json={**payload, "rut": "12345678-5"}).status_code == 201
    # duplicado -> 409 (bug 2.3)
    response = client.post("/companies", json={**payload, "rut": "12345678-5", "email": "otra@y.cl"})
    assert response.status_code == 409
    # email duplicado -> 409
    response = client.post("/companies", json={**payload, "rut": "11111111-1", "email": "x@y.cl"})
    assert response.status_code == 409


def test_availability_windows_are_enforced(client, space, company):
    """Bug 2.1: la disponibilidad horaria ahora se respeta."""
    # 2030-01-10 es jueves
    client.post(
        "/availabilities",
        json={
            "spaceId": space["spaceId"],
            "weekday": "thursday",
            "opening_time": "09:00:00",
            "closing_time": "18:00:00",
        },
    )
    inside = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-10T10:00:00", end="2030-01-10T12:00:00"
    )
    assert inside.status_code == 201
    outside = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-17T03:00:00", end="2030-01-17T05:00:00"
    )
    assert outside.status_code == 400
    assert "availability window" in outside.json()["error"]["message"]


def test_availability_no_overlapping_windows(client, space):
    """Bug 2.2: ventanas solapadas mismo espacio+día -> 409."""
    first = client.post(
        "/availabilities",
        json={"spaceId": space["spaceId"], "weekday": "monday", "opening_time": "09:00:00", "closing_time": "18:00:00"},
    )
    assert first.status_code == 201
    overlap = client.post(
        "/availabilities",
        json={"spaceId": space["spaceId"], "weekday": "monday", "opening_time": "10:00:00", "closing_time": "12:00:00"},
    )
    assert overlap.status_code == 409
    # ventana no solapada el mismo día sí se permite
    disjoint = client.post(
        "/availabilities",
        json={"spaceId": space["spaceId"], "weekday": "monday", "opening_time": "19:00:00", "closing_time": "21:00:00"},
    )
    assert disjoint.status_code == 201


def test_delete_space_only_blocked_by_active_reservations(client, space, company):
    """Bug 2.6: canceladas/completadas ya no bloquean el borrado; disponibilidades en cascada."""
    reservation = make_reservation(client, space["spaceId"], company["companyId"]).json()
    client.post(
        "/availabilities",
        json={"spaceId": space["spaceId"], "weekday": "monday", "opening_time": "09:00:00", "closing_time": "18:00:00"},
    )
    assert client.delete(f"/spaces/{space['spaceId']}").status_code == 409  # reserva activa
    client.post(f"/reservations/{reservation['reservationId']}/cancel")
    assert client.delete(f"/spaces/{space['spaceId']}").status_code == 204
    # disponibilidades eliminadas en cascada
    assert client.get("/availabilities").json()["total"] == 0
