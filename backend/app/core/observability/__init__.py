"""Observability modules for logging, tracing, metrics, and middleware."""

from backend.app.core.observability.alerts import AlertDispatcher, RequestAlertPolicy
from backend.app.core.observability.logging import (
    REQUEST_ID_HEADER,
    TRACE_ID_HEADER,
    StructuredJSONFormatter,
    configure_observability_logger,
)
from backend.app.core.observability.metrics import RequestMetrics
from backend.app.core.observability.middleware import ObservabilityMiddleware
from backend.app.core.observability.runtime import (
    ObservabilityRuntime,
    create_observability_runtime,
)
from backend.app.core.observability.tracing import (
    OTEL_AVAILABLE,
    TracingState,
    configure_tracing,
)

__all__ = [
    "AlertDispatcher",
    "OTEL_AVAILABLE",
    "ObservabilityMiddleware",
    "ObservabilityRuntime",
    "REQUEST_ID_HEADER",
    "RequestAlertPolicy",
    "RequestMetrics",
    "StructuredJSONFormatter",
    "TRACE_ID_HEADER",
    "TracingState",
    "configure_observability_logger",
    "configure_tracing",
    "create_observability_runtime",
]
