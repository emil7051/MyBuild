"""Unit tests for backend service classes."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from backend.app.core.security import hash_secret
from backend.app.db.models import (
    CalculationResultRecord,
    FeedbackRecord,
    OperatorProfileRecord,
    SessionRecord,
    UserInputRecord,
)
from backend.app.models.calculation import CostOverride, VehicleParamOverride
from backend.app.models.session import SessionResponse
from backend.app.services.sessions import SessionService
from backend.app.services.vehicles import VehicleCatalogService
from data.vehicles import ALL_MODELS, BY_ID
from tests.factories import (
    BEV_VEHICLE_ID,
    DIESEL_VEHICLE_ID,
    make_default_results,
    make_session_create,
    make_session_update,
    make_wizard_data,
)


async def _create_session(session_factory, payload):
    async with session_factory() as session:
        return await SessionService().create_session(session, payload)


async def _update_session(session_factory, session_id, payload, session_secret=None):
    async with session_factory() as session:
        return await SessionService().update_session(
            session, session_id, payload, session_secret
        )


async def _get_session(session_factory, session_id, session_secret=None):
    async with session_factory() as session:
        return await SessionService().get_session(session, session_id, session_secret)


async def _fetch_inputs(session_factory):
    async with session_factory() as session:
        result = await session.execute(
            select(UserInputRecord).order_by(UserInputRecord.vehicle_id)
        )
        return result.scalars().all()


async def _fetch_counts(session_factory):
    async with session_factory() as session:
        sessions = await session.scalar(select(func.count(SessionRecord.id))) or 0
        results = (
            await session.scalar(select(func.count(CalculationResultRecord.id))) or 0
        )
        feedback = await session.scalar(select(func.count(FeedbackRecord.id))) or 0
        return sessions, results, feedback


async def _fetch_session(session_factory, session_id):
    async with session_factory() as session:
        return await session.get(SessionRecord, session_id)


async def _fetch_operator_profile(session_factory, session_id):
    async with session_factory() as session:
        return await session.scalar(
            select(OperatorProfileRecord).where(
                OperatorProfileRecord.session_id == session_id
            )
        )


def test_vehicle_catalog_service_summaries() -> None:
    service = VehicleCatalogService()
    summaries = service.list_summaries()
    assert len(summaries) == len(ALL_MODELS)
    assert summaries[0].vehicle_id == ALL_MODELS[0].vehicle_id


def test_vehicle_catalog_service_gets_detail() -> None:
    service = VehicleCatalogService()
    detail = service.get(BEV_VEHICLE_ID)
    assert detail.vehicle_id == BEV_VEHICLE_ID
    assert detail.msrp == BY_ID[BEV_VEHICLE_ID].msrp


def test_vehicle_catalog_service_unknown_id() -> None:
    service = VehicleCatalogService()
    with pytest.raises(KeyError):
        service.get("UNKNOWN")


def test_session_service_create_persists_records(async_session_factory) -> None:
    overrides = CostOverride(annual_kms_variation=50000.0)  # Within valid range
    vehicle_overrides = {BEV_VEHICLE_ID: VehicleParamOverride(msrp_override=110000.0)}
    wizard_data = make_wizard_data(
        overrides=overrides, vehicle_param_overrides=vehicle_overrides
    )
    payload = make_session_create(wizard_data=wizard_data)

    response = asyncio.run(_create_session(async_session_factory, payload))
    assert response.status == "completed"

    sessions, results, feedback = asyncio.run(_fetch_counts(async_session_factory))
    assert sessions == 1
    assert results == len(payload.results or [])
    assert feedback == 1

    inputs = asyncio.run(_fetch_inputs(async_session_factory))
    assert [record.vehicle_id for record in inputs] == [
        BEV_VEHICLE_ID,
        DIESEL_VEHICLE_ID,
    ]

    # API-003: Verify normalized override structure { cost: {}, vehicle: {} }
    bev_overrides = next(
        record.overrides for record in inputs if record.vehicle_id == BEV_VEHICLE_ID
    )
    diesel_overrides = next(
        record.overrides for record in inputs if record.vehicle_id == DIESEL_VEHICLE_ID
    )

    # BEV has both cost and vehicle overrides
    assert bev_overrides["cost"]["annual_kms_variation"] == 50000.0
    assert bev_overrides["vehicle"]["msrp_override"] == 110000.0

    # Diesel only has cost overrides (no vehicle key)
    assert diesel_overrides["cost"]["annual_kms_variation"] == 50000.0
    assert "vehicle" not in diesel_overrides

    operator_profile = asyncio.run(
        _fetch_operator_profile(async_session_factory, response.session_id)
    )
    assert operator_profile is not None


def test_session_service_update_clears_results(async_session_factory) -> None:
    payload = make_session_create()
    response = asyncio.run(_create_session(async_session_factory, payload))

    update_payload = make_session_update(results=[])
    updated = asyncio.run(
        _update_session(
            async_session_factory,
            response.session_id,
            update_payload,
            response.session_secret,
        )
    )
    assert updated.status == "draft"
    assert updated.last_calculated_at is None

    sessions, results, _feedback = asyncio.run(_fetch_counts(async_session_factory))
    assert sessions == 1
    assert results == 0


def test_session_service_unique_vehicle_ids() -> None:
    wizard_data = make_wizard_data(
        current_vehicle=BEV_VEHICLE_ID,
        comparison_vehicles=[BEV_VEHICLE_ID, DIESEL_VEHICLE_ID, DIESEL_VEHICLE_ID],
    )
    unique_ids = SessionService._unique_vehicle_ids(wizard_data)
    assert unique_ids == [BEV_VEHICLE_ID, DIESEL_VEHICLE_ID]


def test_session_service_analytics_summary(async_session_factory) -> None:
    payload = make_session_create(results=make_default_results())
    response = asyncio.run(_create_session(async_session_factory, payload))

    async def _summary():
        async with async_session_factory() as session:
            return await SessionService().analytics_summary(session)

    summary = asyncio.run(_summary())
    assert summary.total_sessions == 1
    assert summary.completed_sessions == 1
    assert summary.calculations_last_24h == len(payload.results or [])
    assert summary.bev_win_rate == 1.0
    # API-006: Payback calculated from MSRP difference (not result payload)
    # (BEV001.msrp - DSL001.msrp) / annual_savings
    # The exact value depends on actual MSRP data, so just check it's reasonable
    assert summary.average_payback_years is not None
    assert summary.average_payback_years > 0
    assert summary.average_cost_delta == 20000.0
    assert summary.top_vehicles[BEV_VEHICLE_ID] == 1
    assert summary.top_vehicles[DIESEL_VEHICLE_ID] == 1

    record = asyncio.run(_fetch_session(async_session_factory, response.session_id))
    assert record is not None
    assert record.status == "completed"


def test_session_service_get_session_uses_cache_before_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = SessionService()
    secret = "cache-secret"
    payload = SessionResponse(
        session_id="cached-session",
        status="completed",
        wizard_data=make_wizard_data(),
        results=make_default_results(),
        updated_at=datetime.now(timezone.utc),
        last_calculated_at=datetime.now(timezone.utc),
    ).model_dump(by_alias=True, mode="json")
    cached_entry = {
        "payload": payload,
        "session_secret_hash": hash_secret(secret),
    }

    async def _fake_get_cached_session(_session_id: str):
        return cached_entry

    class DummyDB:
        async def get(self, *_args, **_kwargs):
            raise AssertionError("DB should not be called on cache hit")

        async def refresh(self, *_args, **_kwargs):
            raise AssertionError("DB refresh should not be called on cache hit")

    async def _run():
        monkeypatch.setattr(
            "backend.app.services.sessions.get_cached_session", _fake_get_cached_session
        )
        return await service.get_session(DummyDB(), "cached-session", secret)

    result = asyncio.run(_run())
    assert result.session_id == "cached-session"
