"""Tests for custom middleware behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator
import logging

from fastapi import FastAPI
import httpx
import pytest

from backend.app.core import config
from backend.app.core.middleware import RequestSizeLimitMiddleware
from backend.app.core.observability import (
    OTEL_AVAILABLE,
    TRACE_ID_HEADER,
    ObservabilityMiddleware,
    RequestAlertPolicy,
    create_observability_runtime,
)


class _ChunkedBody(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk

    async def aclose(self) -> None:
        return None


@pytest.fixture()
def middleware_app(monkeypatch: pytest.MonkeyPatch) -> tuple[FastAPI, dict[str, int]]:
    """Build a test app with a small request size limit."""
    monkeypatch.setattr(config.settings, "max_request_body_size", 64)

    app = FastAPI()
    app.add_middleware(RequestSizeLimitMiddleware)
    side_effects = {"writes": 0}

    @app.post("/write")
    async def write(payload: dict) -> dict[str, str]:
        side_effects["writes"] += 1
        return {"status": "ok", "received": str(payload.get("payload", ""))}

    return app, side_effects


@pytest.fixture()
async def middleware_client(middleware_app: tuple[FastAPI, dict[str, int]]):
    app, _ = middleware_app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture()
def observability_runtime():
    runtime = create_observability_runtime()
    runtime.request_metrics.reset()
    yield runtime
    runtime.request_metrics.reset()


@pytest.fixture()
def observability_app(observability_runtime) -> FastAPI:
    """Build a test app with observability middleware."""
    app = FastAPI()
    app.add_middleware(
        ObservabilityMiddleware,
        logger=observability_runtime.logger,
        metrics=observability_runtime.request_metrics,
        tracing_state=observability_runtime.tracing_state,
        tracer=observability_runtime.tracer,
        slow_request_threshold_ms=config.settings.observability_slow_request_threshold_ms,
        api_v1_prefix=config.settings.api_v1_prefix,
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/sessions")
    async def create_session() -> dict[str, str]:
        return {"status": "created"}

    @app.get("/api/v1/error")
    async def always_fails() -> dict[str, str]:
        raise RuntimeError("boom")

    return app


@pytest.fixture()
async def observability_client(observability_app: FastAPI):
    transport = httpx.ASGITransport(app=observability_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.mark.anyio
async def test_rejects_oversized_content_length_before_handler(
    middleware_app: tuple[FastAPI, dict[str, int]],
    middleware_client: httpx.AsyncClient,
) -> None:
    _, side_effects = middleware_app
    response = await middleware_client.post("/write", json={"payload": "x" * 256})

    assert response.status_code == 413
    assert "Max size: 64 bytes" in response.json()["detail"]
    assert side_effects["writes"] == 0


@pytest.mark.anyio
async def test_rejects_oversized_chunked_body_before_handler(
    middleware_app: tuple[FastAPI, dict[str, int]],
    middleware_client: httpx.AsyncClient,
) -> None:
    _, side_effects = middleware_app
    chunked_payload = _ChunkedBody([b'{"payload":"', b"x" * 40, b"x" * 40, b'"}'])

    response = await middleware_client.post(
        "/write",
        content=chunked_payload,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert side_effects["writes"] == 0


@pytest.mark.anyio
async def test_allows_request_within_limit(
    middleware_app: tuple[FastAPI, dict[str, int]],
    middleware_client: httpx.AsyncClient,
) -> None:
    _, side_effects = middleware_app
    response = await middleware_client.post("/write", json={"payload": "ok"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert side_effects["writes"] == 1


@pytest.mark.anyio
async def test_observability_adds_request_id_header_and_tracks_api_metrics(
    observability_client: httpx.AsyncClient,
    observability_runtime,
) -> None:
    response = await observability_client.post("/api/v1/sessions")

    assert response.status_code == 200
    assert response.headers.get("x-request-id")

    snapshot = observability_runtime.request_metrics.snapshot()
    assert snapshot["requests"] == 1
    assert snapshot["errors"] == 0
    assert snapshot["routes"]["sessions"]["requests"] == 1


@pytest.mark.anyio
@pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry runtime not installed.")
async def test_observability_adds_trace_id_header(
    observability_client: httpx.AsyncClient,
) -> None:
    response = await observability_client.post("/api/v1/sessions")

    assert response.status_code == 200
    trace_id = response.headers.get(TRACE_ID_HEADER)
    assert trace_id is not None
    assert len(trace_id) == 32


@pytest.mark.anyio
async def test_observability_skips_non_api_paths(
    observability_client: httpx.AsyncClient,
    observability_runtime,
) -> None:
    response = await observability_client.get("/")

    assert response.status_code == 200
    assert response.headers.get("x-request-id") is None
    assert observability_runtime.request_metrics.snapshot()["requests"] == 0


@pytest.mark.anyio
async def test_observability_counts_server_errors(
    observability_client: httpx.AsyncClient,
    observability_runtime,
) -> None:
    response = await observability_client.get("/api/v1/error")

    assert response.status_code == 500
    snapshot = observability_runtime.request_metrics.snapshot()
    assert snapshot["requests"] == 1
    assert snapshot["errors"] == 1


@pytest.mark.anyio
async def test_observability_emits_alert_event_for_error_rate_breach(
    observability_client: httpx.AsyncClient,
    observability_runtime,
) -> None:
    captured_records: list[logging.LogRecord] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_records.append(record)

    capture_handler = _CaptureHandler()
    observability_runtime.logger.addHandler(capture_handler)

    original_policy = observability_runtime.request_metrics.alert_policy
    original_dispatcher = observability_runtime.request_metrics.alert_dispatcher
    original_emit_at = observability_runtime.request_metrics._next_emit_at

    try:
        observability_runtime.request_metrics.alert_policy = RequestAlertPolicy(
            min_requests=1,
            error_rate_threshold=0.5,
            avg_duration_ms_threshold=100_000,
            cooldown_seconds=60,
        )
        observability_runtime.request_metrics.alert_dispatcher = None
        observability_runtime.request_metrics._next_emit_at = 0.0

        response = await observability_client.get("/api/v1/error")
        assert response.status_code == 500
    finally:
        observability_runtime.request_metrics.alert_policy = original_policy
        observability_runtime.request_metrics.alert_dispatcher = original_dispatcher
        observability_runtime.request_metrics._next_emit_at = original_emit_at
        observability_runtime.logger.removeHandler(capture_handler)
        observability_runtime.request_metrics.reset()

    alert_records = [
        record
        for record in captured_records
        if getattr(record, "event", "") == "http.alert"
    ]
    assert alert_records
