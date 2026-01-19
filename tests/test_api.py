"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import (
    BEV_VEHICLE_ID,
    make_session_payload_dict,
    make_session_update_payload_dict,
)


def test_healthcheck(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_vehicle_endpoints(client: TestClient) -> None:
    list_response = client.get("/api/v1/vehicles")
    assert list_response.status_code == 200
    vehicles = list_response.json()
    assert vehicles

    vehicle_id = vehicles[0]["vehicle_id"]
    detail_response = client.get(f"/api/v1/vehicles/{vehicle_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["vehicle_id"] == vehicle_id


def test_vehicle_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/vehicles/UNKNOWN")
    assert response.status_code == 404


def test_session_create_and_get(client: TestClient) -> None:
    payload = make_session_payload_dict()
    create_response = client.post("/api/v1/sessions", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "completed"

    session_id = created["sessionId"]
    get_response = client.get(f"/api/v1/sessions/{session_id}")
    assert get_response.status_code == 200
    assert get_response.json()["sessionId"] == session_id


def test_session_update_clears_results(client: TestClient) -> None:
    create_response = client.post("/api/v1/sessions", json=make_session_payload_dict())
    session_id = create_response.json()["sessionId"]

    update_payload = make_session_update_payload_dict(results=[])
    update_response = client.put(f"/api/v1/sessions/{session_id}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "draft"


def test_analytics_summary(client: TestClient) -> None:
    client.post("/api/v1/sessions", json=make_session_payload_dict())

    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["totalSessions"] == 1
    assert summary["completedSessions"] == 1
    assert summary["topVehicles"][BEV_VEHICLE_ID] == 1
