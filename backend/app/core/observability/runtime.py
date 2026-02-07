"""Runtime wiring for observability dependencies."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from backend.app.core.config import settings
from backend.app.core.observability.alerts import AlertDispatcher, RequestAlertPolicy
from backend.app.core.observability.logging import configure_observability_logger
from backend.app.core.observability.metrics import RequestMetrics
from backend.app.core.observability.tracing import (
    TracingState,
    configure_tracing,
    get_request_tracer,
)


@dataclass(frozen=True)
class ObservabilityRuntime:
    logger: logging.Logger
    tracing_state: TracingState
    tracer: Any | None
    request_metrics: RequestMetrics
    alert_dispatcher: AlertDispatcher


def create_observability_runtime() -> ObservabilityRuntime:
    logger = configure_observability_logger()
    tracing_state = configure_tracing(logger)
    alert_dispatcher = AlertDispatcher(
        logger=logger,
        webhook_url=settings.observability_alert_webhook_url,
        timeout_seconds=settings.observability_alert_webhook_timeout_seconds,
    )
    request_metrics = RequestMetrics(
        logger=logger,
        emit_interval_seconds=settings.observability_metrics_emit_interval_seconds,
        alert_policy=RequestAlertPolicy(
            min_requests=settings.observability_alert_min_requests,
            error_rate_threshold=settings.observability_alert_error_rate_threshold,
            avg_duration_ms_threshold=settings.observability_alert_avg_duration_ms_threshold,
            cooldown_seconds=settings.observability_alert_cooldown_seconds,
        ),
        alert_dispatcher=alert_dispatcher,
    )
    tracer = get_request_tracer(tracing_state)
    return ObservabilityRuntime(
        logger=logger,
        tracing_state=tracing_state,
        tracer=tracer,
        request_metrics=request_metrics,
        alert_dispatcher=alert_dispatcher,
    )
