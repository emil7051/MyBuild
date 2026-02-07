"""Tracing configuration helpers for backend observability."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import sys
from typing import Any

from backend.app.core.config import settings

try:
    from opentelemetry import propagate, trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
    from opentelemetry.trace import SpanKind, Status, StatusCode

    OTEL_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - optional dependency at runtime
    propagate = None
    trace = None
    OTLPSpanExporter = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    ConsoleSpanExporter = None
    SimpleSpanProcessor = None
    ParentBased = None
    TraceIdRatioBased = None
    SpanKind = None
    Status = None
    StatusCode = None
    OTEL_AVAILABLE = False


@dataclass
class TracingState:
    configured: bool = False
    enabled: bool = False
    exporter: str = "none"
    sample_rate: float = 0.0


def parse_otlp_headers(raw_headers: str | None) -> dict[str, str]:
    if not raw_headers:
        return {}
    parsed_headers: dict[str, str] = {}
    for header in raw_headers.split(","):
        key, separator, value = header.partition("=")
        if not separator:
            continue
        cleaned_key = key.strip()
        cleaned_value = value.strip()
        if cleaned_key and cleaned_value:
            parsed_headers[cleaned_key] = cleaned_value
    return parsed_headers


_tracing_state: TracingState | None = None


def configure_tracing(logger: logging.Logger) -> TracingState:
    """Configure sampled tracing and return active tracing state."""
    global _tracing_state
    if _tracing_state is not None:
        return _tracing_state

    state = TracingState(
        configured=True, sample_rate=settings.observability_tracing_sample_rate
    )
    if not settings.observability_tracing_enabled or state.sample_rate <= 0:
        state.exporter = "disabled"
        _tracing_state = state
        logger.info(
            "tracing.configured",
            extra={
                "event": "tracing.configured",
                "enabled": False,
                "sample_rate": state.sample_rate,
                "exporter": state.exporter,
            },
        )
        return state

    if not OTEL_AVAILABLE:
        state.exporter = "missing_dependency"
        _tracing_state = state
        logger.warning(
            "tracing.dependencies_missing",
            extra={
                "event": "tracing.configured",
                "enabled": False,
                "sample_rate": state.sample_rate,
                "exporter": state.exporter,
            },
        )
        return state

    try:
        otlp_headers = parse_otlp_headers(settings.observability_tracing_otlp_headers)
        if settings.observability_tracing_otlp_endpoint:
            span_exporter = OTLPSpanExporter(
                endpoint=settings.observability_tracing_otlp_endpoint,
                headers=otlp_headers or None,
            )
            span_processor = BatchSpanProcessor(span_exporter)
            exporter_name = "otlp_http"
        else:
            span_exporter = ConsoleSpanExporter(out=sys.stdout)
            span_processor = SimpleSpanProcessor(span_exporter)
            exporter_name = "console"

        tracer_provider = TracerProvider(
            sampler=ParentBased(TraceIdRatioBased(state.sample_rate)),
            resource=Resource.create(
                {
                    "service.name": settings.observability_tracing_service_name,
                    "deployment.environment": settings.environment,
                }
            ),
        )
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)

        state.enabled = True
        state.exporter = exporter_name
        _tracing_state = state
        logger.info(
            "tracing.configured",
            extra={
                "event": "tracing.configured",
                "enabled": True,
                "sample_rate": state.sample_rate,
                "exporter": state.exporter,
            },
        )
        return state
    except Exception:
        state.exporter = "configuration_failed"
        _tracing_state = state
        logger.exception(
            "tracing.configuration_failed",
            extra={
                "event": "tracing.configured",
                "enabled": False,
                "sample_rate": state.sample_rate,
                "exporter": state.exporter,
            },
        )
        return state


def get_request_tracer(tracing_state: TracingState) -> Any | None:
    if tracing_state.enabled and OTEL_AVAILABLE and trace is not None:
        return trace.get_tracer("backend.observability")
    return None


def current_trace_identifiers() -> tuple[str | None, str | None]:
    if not OTEL_AVAILABLE or trace is None:
        return None, None
    current_span = trace.get_current_span()
    span_context = current_span.get_span_context()
    if not span_context.is_valid:
        return None, None
    return f"{span_context.trace_id:032x}", f"{span_context.span_id:016x}"
