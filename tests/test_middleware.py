"""Tests for custom middleware behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import FastAPI
import httpx
import pytest

from backend.app.core import config
from backend.app.core.middleware import RequestSizeLimitMiddleware
from backend.app.core.observability import ObservabilityMiddleware, request_metrics


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
def observability_app() -> FastAPI:
    """Build a test app with observability middleware."""
    request_metrics.reset()

    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)

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
) -> None:
    response = await observability_client.post("/api/v1/sessions")

    assert response.status_code == 200
    assert response.headers.get("x-request-id")

    snapshot = request_metrics.snapshot()
    assert snapshot["requests"] == 1
    assert snapshot["errors"] == 0
    assert snapshot["routes"]["sessions"]["requests"] == 1


@pytest.mark.anyio
async def test_observability_skips_non_api_paths(
    observability_client: httpx.AsyncClient,
) -> None:
    response = await observability_client.get("/")

    assert response.status_code == 200
    assert response.headers.get("x-request-id") is None
    assert request_metrics.snapshot()["requests"] == 0


@pytest.mark.anyio
async def test_observability_counts_server_errors(
    observability_client: httpx.AsyncClient,
) -> None:
    response = await observability_client.get("/api/v1/error")

    assert response.status_code == 500
    snapshot = request_metrics.snapshot()
    assert snapshot["requests"] == 1
    assert snapshot["errors"] == 1
