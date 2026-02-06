"""Low-overhead observability utilities for API request paths."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

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
except ModuleNotFoundError:
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


def _parse_otlp_headers(raw_headers: str | None) -> dict[str, str]:
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


@dataclass
class TracingState:
    configured: bool = False
    enabled: bool = False
    exporter: str = "none"
    sample_rate: float = 0.0


@dataclass(frozen=True)
class RequestAlertPolicy:
    min_requests: int
    error_rate_threshold: float
    avg_duration_ms_threshold: float
    cooldown_seconds: int


class AlertDispatcher:
    """Dispatch structured alert payloads to an optional webhook."""

    def __init__(
        self,
        logger: logging.Logger,
        webhook_url: str | None,
        timeout_seconds: float = 2.0,
    ) -> None:
        self.logger = logger
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds
        self._executor: ThreadPoolExecutor | None = None
        if self.webhook_url:
            self._executor = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="alert-webhook"
            )

    def dispatch(self, payload: Mapping[str, Any]) -> None:
        if not self.webhook_url or not self._executor:
            return
        self._executor.submit(self._send_webhook, dict(payload))

    def _send_webhook(self, payload: dict[str, Any]) -> None:
        if not self.webhook_url:
            return
        try:
            encoded_payload = json.dumps(payload).encode("utf-8")
            request = Request(
                self.webhook_url,
                data=encoded_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=self.timeout_seconds):
                return
        except URLError:
            self.logger.warning(
                "http.alert.webhook_failed",
                extra={
                    "event": "http.alert.webhook_failed",
                    "webhook_url": self.webhook_url,
                },
            )
        except Exception:
            self.logger.exception(
                "http.alert.webhook_error",
                extra={"event": "http.alert.webhook_error"},
            )


_tracing_state: TracingState | None = None


def configure_tracing() -> TracingState:
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
        observability_logger.info(
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
        observability_logger.warning(
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
        otlp_headers = _parse_otlp_headers(settings.observability_tracing_otlp_headers)
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
        observability_logger.info(
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
        observability_logger.exception(
            "tracing.configuration_failed",
            extra={
                "event": "tracing.configured",
                "enabled": False,
                "sample_rate": state.sample_rate,
                "exporter": state.exporter,
            },
        )
        return state


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


def _current_trace_identifiers() -> tuple[str | None, str | None]:
    if not OTEL_AVAILABLE or trace is None:
        return None, None
    current_span = trace.get_current_span()
    span_context = current_span.get_span_context()
    if not span_context.is_valid:
        return None, None
    return f"{span_context.trace_id:032x}", f"{span_context.span_id:016x}"


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


observability_logger = configure_observability_logger()
configure_tracing()
alert_dispatcher = AlertDispatcher(
    logger=observability_logger,
    webhook_url=settings.observability_alert_webhook_url,
    timeout_seconds=settings.observability_alert_webhook_timeout_seconds,
)
request_metrics = RequestMetrics(
    logger=observability_logger,
    emit_interval_seconds=settings.observability_metrics_emit_interval_seconds,
    alert_policy=RequestAlertPolicy(
        min_requests=settings.observability_alert_min_requests,
        error_rate_threshold=settings.observability_alert_error_rate_threshold,
        avg_duration_ms_threshold=settings.observability_alert_avg_duration_ms_threshold,
        cooldown_seconds=settings.observability_alert_cooldown_seconds,
    ),
    alert_dispatcher=alert_dispatcher,
)


class ObservabilityMiddleware:
    """Request-level logs, tracing, and metric summaries for API traffic only."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = observability_logger
        self.metrics = request_metrics
        self.slow_request_threshold_ms = (
            settings.observability_slow_request_threshold_ms
        )
        self.tracing_state = configure_tracing()
        self.tracer = (
            trace.get_tracer("backend.observability")
            if self.tracing_state.enabled and OTEL_AVAILABLE and trace is not None
            else None
        )

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
        request_headers = Headers(scope=scope)
        request_id = request_headers.get(REQUEST_ID_HEADER) or uuid4().hex
        status_code = 500
        start_ns = time.perf_counter_ns()

        span_context = nullcontext(None)
        if (
            self.tracer is not None
            and OTEL_AVAILABLE
            and propagate is not None
            and SpanKind is not None
        ):
            extracted_context = propagate.extract(dict(request_headers.items()))
            span_context = self.tracer.start_as_current_span(
                f"{method} {route_group}",
                context=extracted_context,
                kind=SpanKind.SERVER,
            )

        with span_context as request_span:
            trace_id, span_id = _current_trace_identifiers()

            async def send_wrapper(message: Message) -> None:
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = int(message["status"])
                    headers = MutableHeaders(raw=message["headers"])
                    if REQUEST_ID_HEADER not in headers:
                        headers.append(REQUEST_ID_HEADER, request_id)
                    if trace_id and TRACE_ID_HEADER not in headers:
                        headers.append(TRACE_ID_HEADER, trace_id)
                await send(message)

            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as exc:
                duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
                self.metrics.record(route_group, 500, duration_ms)
                if (
                    request_span is not None
                    and Status is not None
                    and StatusCode is not None
                ):
                    request_span.record_exception(exc)
                    request_span.set_status(Status(StatusCode.ERROR))
                    request_span.set_attribute("http.status_code", 500)
                self.logger.exception(
                    "http.request.error",
                    extra={
                        "event": "http.request",
                        "request_id": request_id,
                        "trace_id": trace_id,
                        "span_id": span_id,
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

            if request_span is not None:
                request_span.set_attribute("http.method", method)
                request_span.set_attribute("http.route_group", route_group)
                request_span.set_attribute("http.target", path)
                request_span.set_attribute("http.status_code", status_code)
                request_span.set_attribute("request.id", request_id)

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
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "method": method,
                    "path": path,
                    "route_group": route_group,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "slow": is_slow,
                },
            )
