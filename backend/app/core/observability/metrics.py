"""Request metric aggregation helpers for observability middleware."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
import logging
import time
from typing import Any

from backend.app.core.observability.alerts import AlertDispatcher, RequestAlertPolicy


@dataclass
class _RouteMetrics:
    requests: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0


class RequestMetrics:
    """In-memory request metrics with periodic summary logging and alerts."""

    def __init__(
        self,
        logger: logging.Logger,
        emit_interval_seconds: int = 60,
        alert_policy: RequestAlertPolicy | None = None,
        alert_dispatcher: AlertDispatcher | None = None,
    ) -> None:
        self.logger = logger
        self.emit_interval_seconds = max(10, emit_interval_seconds)
        self.alert_policy = alert_policy
        self.alert_dispatcher = alert_dispatcher
        self._next_alert_at = 0.0
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
                metrics.total_duration_ms / metrics.requests
                if metrics.requests
                else 0.0
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
        self._emit_alert_if_needed(snapshot, window_seconds, now)
        self.reset()

    def _emit_alert_if_needed(
        self, snapshot: Mapping[str, Any], window_seconds: float, now: float
    ) -> None:
        if not self.alert_policy:
            return
        request_count = int(snapshot["requests"])
        error_count = int(snapshot["errors"])
        avg_duration_ms = float(snapshot["avg_duration_ms"])

        if request_count < self.alert_policy.min_requests:
            return

        error_rate = error_count / request_count if request_count else 0.0
        breach_types: list[str] = []
        if error_rate >= self.alert_policy.error_rate_threshold:
            breach_types.append("error_rate")
        if avg_duration_ms >= self.alert_policy.avg_duration_ms_threshold:
            breach_types.append("latency")
        if not breach_types or now < self._next_alert_at:
            return

        severity = (
            "critical"
            if error_rate >= max(self.alert_policy.error_rate_threshold * 2, 0.5)
            else "warning"
        )
        alert_payload: dict[str, Any] = {
            "event": "http.alert",
            "severity": severity,
            "breaches": breach_types,
            "window_seconds": round(window_seconds, 2),
            "request_count": request_count,
            "error_count": error_count,
            "error_rate": round(error_rate, 3),
            "avg_duration_ms": round(avg_duration_ms, 2),
            "routes": snapshot["routes"],
        }
        self.logger.warning("http.alert", extra=alert_payload)
        if self.alert_dispatcher:
            self.alert_dispatcher.dispatch(alert_payload)
        self._next_alert_at = now + self.alert_policy.cooldown_seconds
