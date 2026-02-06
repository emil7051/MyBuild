"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from tests.factories import (
    BEV_VEHICLE_ID,
    make_session_payload_dict,
    make_session_update_payload_dict,
)


@pytest.mark.anyio
async def test_healthcheck(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_spa_traversal_blocked(
    async_session_factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.app.db.session import get_db_session
    import backend.app.main as main_module
    from backend.app.main import create_app

    frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    created_dist = False
    created_index = False
    if not frontend_dist.exists():
        frontend_dist.mkdir(parents=True)
        created_dist = True

    index_path = frontend_dist / "index.html"
    if not index_path.exists():
        index_path.write_text("<!doctype html><title>Test</title>", encoding="utf-8")
        created_index = True

    try:

        async def _override_get_db_session():
            async with async_session_factory() as session:
                yield session

        async def _noop_init_db() -> None:
            return None

        monkeypatch.setattr(main_module, "init_db", _noop_init_db)
        application = create_app()
        application.dependency_overrides[get_db_session] = _override_get_db_session

        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            response = await async_client.get("/%2e%2e/package.json")

        assert response.status_code == 200
        assert response.text == index_path.read_text(encoding="utf-8")
    finally:
        if created_index:
            index_path.unlink()
        if created_dist:
            frontend_dist.rmdir()


@pytest.mark.anyio
async def test_vehicle_endpoints(client: httpx.AsyncClient) -> None:
    list_response = await client.get("/api/v1/vehicles")
    assert list_response.status_code == 200
    vehicles = list_response.json()
    assert vehicles

    vehicle_id = vehicles[0]["vehicle_id"]
    detail_response = await client.get(f"/api/v1/vehicles/{vehicle_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["vehicle_id"] == vehicle_id


@pytest.mark.anyio
async def test_vehicle_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/vehicles/UNKNOWN")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_vehicle_endpoint_rate_limit_enforced(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.app.core import config

    monkeypatch.setattr(config.settings, "rate_limit_vehicles_per_minute", 1)
    monkeypatch.setattr(config.settings, "trusted_proxies", ["127.0.0.1"])
    headers = {"X-Forwarded-For": "203.0.113.77"}

    first_response = await client.get("/api/v1/vehicles", headers=headers)
    second_response = await client.get("/api/v1/vehicles", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert "rate limit exceeded" in second_response.text.lower()


@pytest.mark.anyio
async def test_session_create_and_get(client: httpx.AsyncClient) -> None:
    from backend.app.core import config

    payload = make_session_payload_dict()
    create_response = await client.post("/api/v1/sessions", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "completed"
    assert "sessionSecret" not in created

    session_id = created["sessionId"]

    cookie_name = config.settings.session_secret_cookie_name
    session_secret = client.cookies.get(cookie_name)
    assert session_secret
    assert client.cookies.get(cookie_name) == session_secret

    # Clear cookies to confirm secret is still required
    client.cookies.clear()
    get_response_missing = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_response_missing.status_code == 401

    # Cookie-based access
    client.cookies.set(cookie_name, session_secret)
    get_response_cookie = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_response_cookie.status_code == 200
    assert get_response_cookie.json()["sessionId"] == session_id
    assert "sessionSecret" not in get_response_cookie.json()


@pytest.mark.anyio
async def test_session_update_clears_results(client: httpx.AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/sessions", json=make_session_payload_dict()
    )
    created = create_response.json()
    session_id = created["sessionId"]

    update_payload = make_session_update_payload_dict(results=[])
    update_response = await client.put(
        f"/api/v1/sessions/{session_id}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "draft"


@pytest.mark.anyio
async def test_session_update_requires_secret_cookie(client: httpx.AsyncClient) -> None:
    from backend.app.core import config

    create_response = await client.post(
        "/api/v1/sessions", json=make_session_payload_dict()
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["sessionId"]

    client.cookies.clear()
    update_response = await client.put(
        f"/api/v1/sessions/{session_id}",
        json=make_session_update_payload_dict(),
    )

    assert update_response.status_code == 401
    assert "session secret required" in update_response.json()["detail"].lower()

    cookie_name = config.settings.session_secret_cookie_name
    assert client.cookies.get(cookie_name) is None


@pytest.mark.anyio
async def test_session_update_rejects_wrong_secret_cookie(
    client: httpx.AsyncClient,
) -> None:
    from backend.app.core import config

    create_response = await client.post(
        "/api/v1/sessions", json=make_session_payload_dict()
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["sessionId"]

    cookie_name = config.settings.session_secret_cookie_name
    client.cookies.set(cookie_name, "incorrect-session-secret")

    update_response = await client.put(
        f"/api/v1/sessions/{session_id}",
        json=make_session_update_payload_dict(),
    )

    assert update_response.status_code == 403
    assert "invalid session secret" in update_response.json()["detail"].lower()


@pytest.mark.anyio
async def test_analytics_summary(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await client.post("/api/v1/sessions", json=make_session_payload_dict())

    from backend.app.core import config

    monkeypatch.setattr(config.settings, "analytics_api_key", "test-api-key-12345")

    response = await client.get(
        "/api/v1/analytics/summary",
        headers={"X-Analytics-Key": "test-api-key-12345"},
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["totalSessions"] == 1
    assert summary["completedSessions"] == 1
    assert summary["topVehicles"][BEV_VEHICLE_ID] == 1
