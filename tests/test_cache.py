"""Tests for Redis cache initialization behavior."""

from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.enable_redis_cache


def test_redis_client_retries_after_failure(monkeypatch) -> None:
    from backend.app.core import cache

    class DummyRedis:
        pass

    calls = {"count": 0}

    def _fake_from_url(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("redis down")
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
