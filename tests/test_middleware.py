"""Tests for custom request-size middleware behavior."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import FastAPI
import httpx
import pytest

from backend.app.core import config
from backend.app.core.middleware import RequestSizeLimitMiddleware


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
