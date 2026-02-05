"""Redis cache client for session persistence."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional, TypedDict

import redis.asyncio as redis

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class CachedSession(TypedDict):
    payload: dict[str, Any]
    session_secret_hash: Optional[str]


_redis_client: Optional[redis.Redis] = None
_redis_init_lock = asyncio.Lock()
_next_retry_at = 0.0
_retry_backoff_seconds = 5.0


def _mark_redis_unavailable(exc: Exception) -> None:
    global _redis_client, _next_retry_at
    _redis_client = None
    _next_retry_at = time.monotonic() + _retry_backoff_seconds
    logger.warning("Redis unavailable: %s", exc)


async def _get_redis_client() -> Optional[redis.Redis]:
    global _redis_client, _next_retry_at

    if _redis_client is not None:
        return _redis_client

    if not settings.redis_url:
        return None

    now = time.monotonic()
    if now < _next_retry_at:
        return None

    async with _redis_init_lock:
        if _redis_client is not None:
            return _redis_client
        now = time.monotonic()
        if now < _next_retry_at:
            return None
        try:
            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            return _redis_client
        except Exception as exc:
            _mark_redis_unavailable(exc)
            return None


async def cache_session(
    session_id: str, payload: dict[str, Any], session_secret_hash: str | None
) -> None:
    """Persist wizard session snapshots in Redis for quick resume."""

    client = await _get_redis_client()
    if not client:
        logger.debug("Redis not available, skipping cache for session %s", session_id)
        return

    try:
        cache_entry = {
            "payload": payload,
            "sessionSecretHash": session_secret_hash,
        }
        await client.setex(
            f"session:{session_id}",
            settings.session_ttl_seconds,
            json.dumps(cache_entry),
        )
    except Exception as exc:  # pragma: no cover - cache failures shouldn't break flow
        _mark_redis_unavailable(exc)


async def get_cached_session(session_id: str) -> Optional[CachedSession]:
    """Return a cached session snapshot if present."""

    client = await _get_redis_client()
    if not client:
        logger.debug("Redis not available, returning None for session %s", session_id)
        return None

    try:
        raw = await client.get(f"session:{session_id}")
        if not raw:
            return None
        decoded = json.loads(raw)
        if (
            isinstance(decoded, dict)
            and "payload" in decoded
            and "sessionSecretHash" in decoded
        ):
            return {
                "payload": decoded["payload"],
                "session_secret_hash": decoded.get("sessionSecretHash"),
            }
        # Legacy cache entries without secret hash should be refreshed from DB
        return None
    except Exception as exc:  # pragma: no cover
        _mark_redis_unavailable(exc)
        return None
