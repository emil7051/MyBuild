"""Structured logging helpers for backend observability."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any

REQUEST_ID_HEADER = "x-request-id"
TRACE_ID_HEADER = "x-trace-id"
_RESERVED_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__.keys())


def _normalize_for_json(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_for_json(item) for item in value]
    return str(value)


class StructuredJSONFormatter(logging.Formatter):
    """Render logs as compact JSON for easy ingestion on stdout."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc)
        payload: dict[str, Any] = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_FIELDS:
                continue
            payload[key] = _normalize_for_json(value)
        return json.dumps(payload, separators=(",", ":"))


def configure_observability_logger() -> logging.Logger:
    """Configure and return the observability logger."""
    logger = logging.getLogger("backend.observability")
    if getattr(logger, "_configured", False):
        return logger

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(StructuredJSONFormatter())

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger._configured = True  # type: ignore[attr-defined]
    return logger
