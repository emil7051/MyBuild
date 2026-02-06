"""Tests for Redis cache behavior."""

from __future__ import annotations

import asyncio
import json

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

pytestmark = pytest.mark.enable_redis_cache


def test_redis_client_retries_after_failure(monkeypatch) -> None:
    from backend.app.core import cache

    class DummyRedis:
        pass

    calls = {"count": 0}

    def _fake_from_url(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RedisConnectionError("redis down")
        return DummyRedis()

    monkeypatch.setattr(cache.redis, "from_url", _fake_from_url)
    monkeypatch.setattr(cache.settings, "redis_url", "redis://test", raising=False)
    monkeypatch.setattr(cache, "_retry_backoff_seconds", 0.0)
    monkeypatch.setattr(cache, "_redis_client", None)
    monkeypatch.setattr(cache, "_next_retry_at", 0.0)

    first = asyncio.run(cache._get_redis_client())
    assert first is None

    second = asyncio.run(cache._get_redis_client())
    assert isinstance(second, DummyRedis)


def test_redis_client_does_not_mask_non_redis_errors(monkeypatch) -> None:
    from backend.app.core import cache

    def _fake_from_url(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cache.redis, "from_url", _fake_from_url)
    monkeypatch.setattr(cache.settings, "redis_url", "redis://test", raising=False)
    monkeypatch.setattr(cache, "_retry_backoff_seconds", 0.0)
    monkeypatch.setattr(cache, "_redis_client", None)
    monkeypatch.setattr(cache, "_next_retry_at", 0.0)

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(cache._get_redis_client())

    assert cache._next_retry_at == 0.0


def test_cache_session_propagates_serialization_errors(monkeypatch) -> None:
    from backend.app.core import cache

    class DummyRedis:
        called = False

        async def setex(self, *_args, **_kwargs):
            self.called = True

    client = DummyRedis()

    async def _fake_get_client():
        return client

    monkeypatch.setattr(cache, "_get_redis_client", _fake_get_client)

    with pytest.raises(TypeError):
        asyncio.run(
            cache.cache_session("session-1", {"non_serializable": object()}, None)
        )

    assert client.called is False


def test_cache_session_handles_redis_errors(monkeypatch) -> None:
    from backend.app.core import cache

    class DummyRedis:
        async def setex(self, *_args, **_kwargs):
            raise RedisConnectionError("down")

    seen: list[Exception] = []

    async def _fake_get_client():
        return DummyRedis()

    def _fake_mark(exc):
        seen.append(exc)

    monkeypatch.setattr(cache, "_get_redis_client", _fake_get_client)
    monkeypatch.setattr(cache, "_mark_redis_unavailable", _fake_mark)

    asyncio.run(cache.cache_session("session-1", {"ok": True}, None))

    assert len(seen) == 1
    assert isinstance(seen[0], RedisConnectionError)


def test_get_cached_session_handles_redis_errors(monkeypatch) -> None:
    from backend.app.core import cache

    class DummyRedis:
        async def get(self, *_args, **_kwargs):
            raise RedisConnectionError("down")

    seen: list[Exception] = []

    async def _fake_get_client():
        return DummyRedis()

    def _fake_mark(exc):
        seen.append(exc)

    monkeypatch.setattr(cache, "_get_redis_client", _fake_get_client)
    monkeypatch.setattr(cache, "_mark_redis_unavailable", _fake_mark)

    value = asyncio.run(cache.get_cached_session("session-1"))

    assert value is None
    assert len(seen) == 1
    assert isinstance(seen[0], RedisConnectionError)


def test_get_cached_session_propagates_invalid_json(monkeypatch) -> None:
    from backend.app.core import cache

    class DummyRedis:
        async def get(self, *_args, **_kwargs):
            return "{not-json"

    async def _fake_get_client():
        return DummyRedis()

    monkeypatch.setattr(cache, "_get_redis_client", _fake_get_client)

    with pytest.raises(json.JSONDecodeError):
        asyncio.run(cache.get_cached_session("session-1"))
