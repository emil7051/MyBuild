"""Tests for Phase 4 security features.

TEST-005: Override shape normalization
SEC-003: Backend bounds checking
API-002: UUID validation
API-007: Payload validation
SEC-007: Analytics API key protection
"""

from __future__ import annotations

import httpx
import pytest
from fastapi import HTTPException

from tests.factories import (
    BEV_VEHICLE_ID,
    make_session_payload_dict,
    make_session_update_payload_dict,
)

# ============================================================================
# API-002: UUID validation tests
# ============================================================================


@pytest.mark.anyio
async def test_invalid_uuid_session_get_returns_422(client: httpx.AsyncClient) -> None:
    """Invalid session_id format should return 422."""
    response = await client.get("/api/v1/sessions/not-a-uuid")
    assert response.status_code == 422
    assert "Invalid session_id format" in response.json()["detail"]


@pytest.mark.anyio
async def test_invalid_uuid_session_put_returns_422(client: httpx.AsyncClient) -> None:
    """Invalid session_id format in PUT should return 422."""
    response = await client.put(
        "/api/v1/sessions/invalid-uuid",
        json=make_session_update_payload_dict(),
    )
    assert response.status_code == 422
    assert "Invalid session_id format" in response.json()["detail"]


# ============================================================================
# API-007: Payload validation tests
# ============================================================================


@pytest.mark.anyio
async def test_invalid_scenario_returns_422(client: httpx.AsyncClient) -> None:
    """Unknown scenario should return 422."""
    payload = make_session_payload_dict()
    payload["wizardData"]["scenario"] = "invalid_scenario"
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_invalid_vehicle_id_returns_422(client: httpx.AsyncClient) -> None:
    """Unknown vehicle ID should return 422."""
    payload = make_session_payload_dict()
    payload["wizardData"]["currentVehicle"] = "UNKNOWN_VEHICLE"
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_invalid_email_format_returns_422(client: httpx.AsyncClient) -> None:
    """Invalid email format should return 422."""
    payload = make_session_payload_dict()
    payload["operatorProfile"]["contactEmail"] = "not-an-email"
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_valid_email_format_accepted(client: httpx.AsyncClient) -> None:
    """Valid email format should be accepted."""
    payload = make_session_payload_dict()
    payload["operatorProfile"]["contactEmail"] = "test@example.com"
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201


@pytest.mark.anyio
async def test_duty_cycle_must_sum_to_100(client: httpx.AsyncClient) -> None:
    """Duty cycle must sum to approximately 100%."""
    payload = make_session_payload_dict()
    payload["wizardData"]["dutyCycle"] = {"urban": 10, "regional": 10, "longHaul": 10}
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 422


# ============================================================================
# SEC-003: Backend bounds checking tests
# ============================================================================


@pytest.mark.anyio
async def test_override_out_of_range_returns_422(client: httpx.AsyncClient) -> None:
    """Override values outside valid ranges should return 422."""
    payload = make_session_payload_dict()
    # Set annual_kms_variation below minimum (5000)
    payload["wizardData"]["overrides"] = {"annual_kms_variation": 100}
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_vehicle_param_override_out_of_range_returns_422(
    client: httpx.AsyncClient,
) -> None:
    """Vehicle param override out of range should return 422."""
    payload = make_session_payload_dict()
    # range_km_override minimum is 50
    payload["wizardData"]["vehicleParamOverrides"] = {
        BEV_VEHICLE_ID: {"range_km_override": 10}
    }
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_valid_overrides_accepted(client: httpx.AsyncClient) -> None:
    """Valid override values within range should be accepted."""
    payload = make_session_payload_dict()
    payload["wizardData"]["overrides"] = {
        "annual_kms_variation": 50000,
        "residual_value_variation": 1.0,
        "fuel_price_variation": 1.5,
    }
    payload["wizardData"]["vehicleParamOverrides"] = {
        BEV_VEHICLE_ID: {
            "range_km_override": 200,
            "kwh_per_km_override": 1.5,
        }
    }
    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201


# ============================================================================
# SEC-007: Analytics API key protection tests
# ============================================================================


@pytest.mark.anyio
async def test_analytics_with_api_key_required(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Analytics endpoint should require API key when configured."""
    from backend.app.core import config

    # Configure API key requirement
    monkeypatch.setattr(config.settings, "analytics_api_key", "test-api-key-12345")

    # Request without key should fail
    response_no_key = await client.get("/api/v1/analytics/summary")
    assert response_no_key.status_code == 401

    # Request with wrong key should fail
    response_wrong_key = await client.get(
        "/api/v1/analytics/summary",
        headers={"X-Analytics-Key": "wrong-key"},
    )
    assert response_wrong_key.status_code == 401

    # Request with correct key should succeed
    response_correct_key = await client.get(
        "/api/v1/analytics/summary",
        headers={"X-Analytics-Key": "test-api-key-12345"},
    )
    assert response_correct_key.status_code == 200


@pytest.mark.anyio
async def test_analytics_without_api_key_configured(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Analytics endpoint should be disabled when no API key is configured."""
    from backend.app.core import config

    # Ensure no API key is configured
    monkeypatch.setattr(config.settings, "analytics_api_key", None)

    response = await client.get("/api/v1/analytics/summary")
    assert response.status_code == 403


# ============================================================================
# TEST-005: Override shape normalization tests
# ============================================================================


@pytest.mark.anyio
async def test_override_shape_normalized_in_storage(
    client: httpx.AsyncClient,
    async_session_factory,
) -> None:
    """Overrides should be stored in normalized { cost: {}, vehicle: {} } shape."""
    from sqlalchemy import select

    from backend.app.db.models import UserInputRecord

    payload = make_session_payload_dict()
    payload["wizardData"]["overrides"] = {"fuel_price_variation": 1.2}
    payload["wizardData"]["vehicleParamOverrides"] = {
        BEV_VEHICLE_ID: {"range_km_override": 300}
    }

    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201
    session_id = response.json()["sessionId"]

    # Query the stored user input directly
    async with async_session_factory() as session:
        result = await session.execute(
            select(UserInputRecord).where(
                UserInputRecord.session_id == session_id,
                UserInputRecord.vehicle_id == BEV_VEHICLE_ID,
            )
        )
        user_input = result.scalar_one()

        # Verify normalized structure
        assert user_input.overrides is not None
        assert "cost" in user_input.overrides
        assert "vehicle" in user_input.overrides
        assert user_input.overrides["cost"]["fuel_price_variation"] == 1.2
        assert user_input.overrides["vehicle"]["range_km_override"] == 300


@pytest.mark.anyio
async def test_cost_only_overrides_stored_correctly(
    client: httpx.AsyncClient,
    async_session_factory,
) -> None:
    """Cost overrides without vehicle overrides should be stored correctly."""
    from sqlalchemy import select

    from backend.app.db.models import UserInputRecord

    payload = make_session_payload_dict()
    payload["wizardData"]["overrides"] = {"maintenance_cost_variation": 0.8}
    payload["wizardData"]["vehicleParamOverrides"] = None

    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201
    session_id = response.json()["sessionId"]

    async with async_session_factory() as session:
        result = await session.execute(
            select(UserInputRecord).where(
                UserInputRecord.session_id == session_id,
            )
        )
        user_input = result.scalars().first()

        assert user_input.overrides is not None
        assert "cost" in user_input.overrides
        assert user_input.overrides["cost"]["maintenance_cost_variation"] == 0.8
        # No vehicle key when no vehicle overrides
        assert "vehicle" not in user_input.overrides


@pytest.mark.anyio
async def test_no_overrides_stored_as_none(
    client: httpx.AsyncClient,
    async_session_factory,
) -> None:
    """Session with no overrides should store None in overrides field."""
    from sqlalchemy import select

    from backend.app.db.models import UserInputRecord

    payload = make_session_payload_dict()
    payload["wizardData"]["overrides"] = None
    payload["wizardData"]["vehicleParamOverrides"] = None

    response = await client.post("/api/v1/sessions", json=payload)
    assert response.status_code == 201
    session_id = response.json()["sessionId"]

    async with async_session_factory() as session:
        result = await session.execute(
            select(UserInputRecord).where(
                UserInputRecord.session_id == session_id,
            )
        )
        user_input = result.scalars().first()

        # No overrides should be None
        assert user_input.overrides is None


def test_verify_session_secret_returns_500_on_unexpected_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected bcrypt errors should surface as 500s."""
    from backend.app.core import security

    def _boom(*_args, **_kwargs):
        raise RuntimeError("bcrypt failure")

    monkeypatch.setattr(security.bcrypt, "checkpw", _boom)

    with pytest.raises(HTTPException) as exc_info:
        security.verify_session_secret("secret", "hash")

    assert exc_info.value.status_code == 500
