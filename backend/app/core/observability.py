"""Low-overhead observability utilities for API request paths."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import sys
import time
from typing import Any
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.core.config import settings

REQUEST_ID_HEADER = "x-request-id"
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


def _route_group_for_path(path: str) -> str | None:
    """Map dynamic paths to low-cardinality route groups."""
    api_prefix = settings.api_v1_prefix
    if not path.startswith(api_prefix):
        return None
    if path.startswith(f"{api_prefix}/sessions"):
        return "sessions"
    if path.startswith(f"{api_prefix}/analytics"):
        return "analytics"
    if path.startswith(f"{api_prefix}/vehicles"):
        return "vehicles"
    if path.startswith(f"{api_prefix}/health"):
        return "health"
    return "other"


@dataclass
class _RouteMetrics:
    requests: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0


class RequestMetrics:
    """In-memory request metrics with periodic summary logging."""

    def __init__(self, logger: logging.Logger, emit_interval_seconds: int = 60) -> None:
        self.logger = logger
        self.emit_interval_seconds = max(10, emit_interval_seconds)
        self.reset()

    def reset(self) -> None:
        now = time.monotonic()
        self._window_started_at = now
        self._next_emit_at = now + self.emit_interval_seconds
        self._routes: dict[str, _RouteMetrics] = defaultdict(_RouteMetrics)
        self._total = _RouteMetrics()

    def record(self, route_group: str, status_code: int, duration_ms: float) -> None:
        route_metrics = self._routes[route_group]
        route_metrics.requests += 1
        route_metrics.total_duration_ms += duration_ms
        if status_code >= 500:
            route_metrics.errors += 1

        self._total.requests += 1
        self._total.total_duration_ms += duration_ms
        if status_code >= 500:
            self._total.errors += 1

        now = time.monotonic()
        if now >= self._next_emit_at:
            self._emit_window_summary(now)

    def snapshot(self) -> dict[str, Any]:
        routes: dict[str, dict[str, float | int]] = {}
        for name, metrics in self._routes.items():
            average_duration_ms = (
                metrics.total_duration_ms / metrics.requests if metrics.requests else 0.0
            )
            routes[name] = {
                "requests": metrics.requests,
                "errors": metrics.errors,
                "avg_duration_ms": round(average_duration_ms, 2),
            }

        average_total_duration_ms = (
            self._total.total_duration_ms / self._total.requests
            if self._total.requests
            else 0.0
        )
        return {
            "requests": self._total.requests,
            "errors": self._total.errors,
            "avg_duration_ms": round(average_total_duration_ms, 2),
            "routes": routes,
        }

    def _emit_window_summary(self, now: float) -> None:
        snapshot = self.snapshot()
        window_seconds = max(now - self._window_started_at, 0.001)
        self.logger.info(
            "http.metrics",
            extra={
                "event": "http.metrics",
                "window_seconds": round(window_seconds, 2),
                "request_count": snapshot["requests"],
                "error_count": snapshot["errors"],
                "avg_duration_ms": snapshot["avg_duration_ms"],
                "routes": snapshot["routes"],
            },
        )
        self.reset()


observability_logger = configure_observability_logger()
request_metrics = RequestMetrics(observability_logger)


class ObservabilityMiddleware:
    """Request-level logs and metrics for API traffic only."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = observability_logger
        self.metrics = request_metrics
        self.slow_request_threshold_ms = 750.0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        route_group = _route_group_for_path(path)
        if route_group is None:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        request_id = (
            Headers(scope=scope).get(REQUEST_ID_HEADER) or uuid4().hex
        )
        status_code = 500
        start_ns = time.perf_counter_ns()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = MutableHeaders(raw=message["headers"])
                if REQUEST_ID_HEADER not in headers:
                    headers.append(REQUEST_ID_HEADER, request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            self.metrics.record(route_group, 500, duration_ms)
            self.logger.exception(
                "http.request.error",
                extra={
                    "event": "http.request",
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "route_group": route_group,
                    "status_code": 500,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        self.metrics.record(route_group, status_code, duration_ms)

        is_slow = duration_ms >= self.slow_request_threshold_ms
        should_log = (
            status_code >= 500
            or is_slow
            or method in {"POST", "PUT", "PATCH", "DELETE"}
        )
        if not should_log:
            return

        level = logging.WARNING if status_code >= 500 or is_slow else logging.INFO
        self.logger.log(
            level,
            "http.request",
            extra={
                "event": "http.request",
                "request_id": request_id,
                "method": method,
                "path": path,
                "route_group": route_group,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "slow": is_slow,
            },
        )
