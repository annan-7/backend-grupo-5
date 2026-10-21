"""Contrato HTTP: enveloppe de errores uniforme, paginación, filtros y docs."""

from tests.conftest import make_reservation


def test_error_envelope_is_uniform(client):
    """Todos los errores comparten {"error": {code, message, details}}."""
    cases = [
        client.get("/spaces/nope"),  # 404
        client.post("/spaces", json={"spaceName": "x"}),  # 422 de body
        client.get("/spaces", params={"page": 0}),  # 422 de query
        client.get("/spaces", params={"sort_by": "hack"}),  # 422 de query
        client.get("/no-such-route"),  # 404 de routing
    ]
    expected_codes = [404, 422, 422, 422, 404]
    for response, expected in zip(cases, expected_codes, strict=True):
        assert response.status_code == expected
        body = response.json()
        assert set(body.keys()) == {"error"}
        assert set(body["error"].keys()) == {"code", "message", "details"}
    # los 422 usan SIEMPRE el mismo code (antes: HTTP_ERROR vs VALIDATION_ERROR)
    assert cases[1].json()["error"]["code"] == "VALIDATION_ERROR"
    assert cases[2].json()["error"]["code"] == "VALIDATION_ERROR"
    assert cases[3].json()["error"]["code"] == "VALIDATION_ERROR"


def test_conflict_and_business_codes(client, space, company):
    make_reservation(client, space["spaceId"], company["companyId"])
    conflict = make_reservation(
        client, space["spaceId"], company["companyId"], start="2030-01-10T11:00:00", end="2030-01-10T13:00:00"
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"


def test_pagination_and_filters(client):
    for index in range(5):
        client.post(
            "/spaces",
            json={"spaceName": f"Sala {index}", "type": "meeting_room", "capacity": index + 1, "description": "desc"},
        )
    client.post(
        "/spaces", json={"spaceName": "Oficina", "type": "private_office", "capacity": 3, "description": "desc"}
    )

    page = client.get("/spaces", params={"page": 1, "limit": 2, "sort_by": "capacity", "direction": "asc"})
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 6 and body["totalPages"] == 3 and len(body["items"]) == 2
    assert body["items"][0]["capacity"] == 1

    filtered = client.get("/spaces", params={"type": "private_office"})
    assert filtered.json()["total"] == 1
    filtered = client.get("/spaces", params={"min_capacity": 4})
    assert filtered.json()["total"] == 2
    filtered = client.get("/spaces", params={"status": "active", "type": "meeting_room"})
    assert filtered.json()["total"] == 5


def test_availability_list_has_filters_and_pagination(client, space):
    """Bug 2.8: GET /availabilities ahora filtra y pagina."""
    client.post(
        "/availabilities",
        json={"spaceId": space["spaceId"], "weekday": "monday", "opening_time": "09:00:00", "closing_time": "12:00:00"},
    )
    client.post(
        "/availabilities",
        json={"spaceId": space["spaceId"], "weekday": "friday", "opening_time": "15:00:00", "closing_time": "18:00:00"},
    )
    response = client.get("/availabilities", params={"weekday": "monday"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1 and body["items"][0]["weekday"] == "monday"
    assert client.get("/availabilities", params={"space_id": space["spaceId"]}).json()["total"] == 2
    assert client.get("/availabilities", params={"page": 1, "limit": 1}).json()["totalPages"] == 2


def test_response_fields_are_camel_case(client, space):
    assert {"spaceId", "spaceName", "createdAt", "updatedAt"} <= set(space.keys())
    assert client.get("/spaces/" + space["spaceId"]).status_code == 200


def test_request_accepts_camel_and_snake(client, space, company):
    """populate_by_name: ambos estilos funcionan en el body."""
    camel = make_reservation(client, space["spaceId"], company["companyId"])
    assert camel.status_code == 201
    snake = client.post(
        "/reservations",
        json={
            "space_id": space["spaceId"],
            "company_id": company["companyId"],
            "start_date": "2030-06-10T10:00:00",
            "end_date": "2030-06-10T12:00:00",
            "reason": "En snake case tambien funciona",
        },
    )
    assert snake.status_code == 201


def test_space_type_is_enum_now(client):
    response = client.post(
        "/spaces", json={"spaceName": "Sala X", "type": "no_existe", "capacity": 5, "description": "d"}
    )
    assert response.status_code == 422


def test_empty_description_is_422_not_400(client):
    """La validación de formato vive en el schema (422), no en el dominio (400)."""
    response = client.post(
        "/spaces", json={"spaceName": "Sala X", "type": "meeting_room", "capacity": 5, "description": ""}
    )
    assert response.status_code == 422


def test_transition_endpoints(client, space, company):
    reservation = make_reservation(client, space["spaceId"], company["companyId"]).json()
    rid = reservation["reservationId"]
    assert client.post(f"/reservations/{rid}/confirm").json()["status"] == "confirmed"
    assert client.post(f"/reservations/{rid}/complete").json()["status"] == "completed"
    response = client.post(f"/reservations/{rid}/cancel")
    assert response.status_code == 400  # completada es terminal


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
