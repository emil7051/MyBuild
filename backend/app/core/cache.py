"""Redis cache client for session persistence."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def _create_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


redis_client = _create_client()


async def cache_session(session_id: str, payload: dict[str, Any]) -> None:
    """Persist wizard session snapshots in Redis for quick resume."""

    try:
        await redis_client.setex(
            f"session:{session_id}",
            settings.session_ttl_seconds,
            json.dumps(payload),
        )
    except Exception as exc:  # pragma: no cover - cache failures shouldn't break flow
        logger.warning("Failed to cache session %s: %s", session_id, exc)


async def get_cached_session(session_id: str) -> Optional[dict[str, Any]]:
    """Return a cached session snapshot if present."""

    try:
        raw = await redis_client.get(f"session:{session_id}")
        if not raw:
            return None
        return json.loads(raw)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to fetch cached session %s: %s", session_id, exc)
        return None
