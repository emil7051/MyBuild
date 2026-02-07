"""Redis cache client for session persistence."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional, TypedDict

import redis.asyncio as redis
from redis.exceptions import RedisError

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class CachedSession(TypedDict):
    payload: dict[str, Any]
    session_secret_hash: Optional[str]


_redis_client: Optional[redis.Redis] = None
_redis_init_lock = asyncio.Lock()
_next_retry_at = 0.0
_retry_backoff_seconds = 5.0


def _mark_redis_unavailable(exc: RedisError) -> None:
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
        except RedisError as exc:
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

    cache_entry = {
        "payload": payload,
        "session_secret_hash": session_secret_hash,
    }
    serialized_entry = json.dumps(cache_entry)

    try:
        await client.setex(
            f"session:{session_id}",
            settings.session_ttl_seconds,
            serialized_entry,
        )
    except RedisError as exc:  # pragma: no cover - cache failures shouldn't break flow
        _mark_redis_unavailable(exc)


async def get_cached_session(session_id: str) -> Optional[CachedSession]:
    """Return a cached session snapshot if present."""

    client = await _get_redis_client()
    if not client:
        logger.debug("Redis not available, returning None for session %s", session_id)
        return None

    cache_key = f"session:{session_id}"

    try:
        raw = await client.get(cache_key)
    except RedisError as exc:  # pragma: no cover
        _mark_redis_unavailable(exc)
        return None

    if not raw:
        return None

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(
            "Invalid cached JSON for session %s; evicting corrupted entry.",
            session_id,
        )
        try:
            await client.delete(cache_key)
        except RedisError as exc:  # pragma: no cover
            _mark_redis_unavailable(exc)
        return None

    if isinstance(decoded, dict) and "payload" in decoded:
        session_hash = decoded.get("session_secret_hash")
        # Backward compatibility for legacy cache entries.
        if session_hash is None and "sessionSecretHash" in decoded:
            session_hash = decoded.get("sessionSecretHash")
        if "session_secret_hash" in decoded or "sessionSecretHash" in decoded:
            return {
                "payload": decoded["payload"],
                "session_secret_hash": session_hash,
            }
    # Legacy cache entries without secret hash should be refreshed from DB
    return None
