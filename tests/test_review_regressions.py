"""Regresiones de los bugs críticos detectados en la revisión (sección 🔴)."""

from tests.conftest import make_reservation


def test_package_facades_export_names():
    """Bug 1.2: los __init__.py se auto-importaban y no exportaban nada."""
    from app.domain import Company, Reservation, Space, validate_text  # noqa: F401
    from app.schemas import SpaceCreate, SpaceResponse  # noqa: F401


def test_mixed_naive_and_aware_datetimes_do_not_crash(client, space, company):
    """Bug 1.1: mezclar fechas naive y con timezone daba 500 (TypeError)."""
    first = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-10T10:00:00", end="2030-01-10T12:00:00"
    )
    assert first.status_code == 201
    second = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-11T10:00:00Z", end="2030-01-11T12:00:00+00:00"
    )
    assert second.status_code == 201, second.text


def test_listing_sorts_mixed_timezones(client, space, company):
    make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-10T10:00:00", end="2030-01-10T12:00:00"
    )
    make_reservation(
        client, space["spaceId"], company["companyId"], start="2031-01-10T10:00:00Z", end="2031-01-10T12:00:00Z"
    )
    response = client.get("/reservations", params={"sort_by": "start_date", "direction": "asc"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["startDate"] < items[1]["startDate"]


def test_state_machine_blocks_illegal_transitions(client, space, company):
    """Bug 1.3: PUT permitía completed->pending y canceled->confirmed."""
    reservation = make_reservation(client, space["spaceId"], company["companyId"]).json()
    rid = reservation["reservationId"]

    # pending -> completed no es legal (debe confirmarse antes)
    assert client.put(f"/reservations/{rid}", json={"status": "completed"}).status_code == 400
    # pending -> confirmed -> completed: camino legal
    assert client.put(f"/reservations/{rid}", json={"status": "confirmed"}).status_code == 200
    assert client.put(f"/reservations/{rid}", json={"status": "completed"}).status_code == 200
    # completed es terminal
    response = client.put(f"/reservations/{rid}", json={"status": "pending"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    # canceled es terminal
    reservation2 = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-02-10T10:00:00", end="2030-02-10T12:00:00"
    ).json()
    assert client.post(f"/reservations/{reservation2['reservationId']}/cancel").status_code == 200
    response = client.put(f"/reservations/{reservation2['reservationId']}", json={"status": "confirmed"})
    assert response.status_code == 400


def test_editing_canceled_reservation_does_not_false_conflict(client, space):
    """Bug 1.4: editar el `reason` de una cancelada solapada con una activa daba 409 falso."""
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
    canceled = make_reservation(client, space["spaceId"], company_b["companyId"]).json()
    assert client.post(f"/reservations/{canceled['reservationId']}/cancel").status_code == 200
    # otra empresa reserva el mismo hueco liberado
    active = make_reservation(client, space["spaceId"], company_a["companyId"])
    assert active.status_code == 201
    # editar solo el motivo de la cancelada ya no da 409
    response = client.put(f"/reservations/{canceled['reservationId']}", json={"reason": "Motivo actualizado"})
    assert response.status_code == 200, response.text
    # pero reagendar una cancelada sí está bloqueado
    response = client.put(f"/reservations/{canceled['reservationId']}", json={"start_date": "2030-05-01T10:00:00Z"})
    assert response.status_code == 400


def test_rn1_space_with_future_reservations_cannot_go_inactive(client, space, company):
    """Bug 1.5: un espacio con reservas futuras activas podía pasar a maintenance."""
    assert make_reservation(client, space["spaceId"], company["companyId"]).status_code == 201
    response = client.put(f"/spaces/{space['spaceId']}", json={"status": "maintenance"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"
    # sin reservas futuras (todas canceladas), sí se puede
    reservations = client.get("/reservations").json()["items"]
    for item in reservations:
        client.post(f"/reservations/{item['reservationId']}/cancel")
    assert client.put(f"/spaces/{space['spaceId']}", json={"status": "maintenance"}).status_code == 200
