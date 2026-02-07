"""ASGI middleware for request-level observability."""

from __future__ import annotations

from contextlib import nullcontext
import logging
import time
from typing import Any
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.core.observability.logging import REQUEST_ID_HEADER, TRACE_ID_HEADER
from backend.app.core.observability.metrics import RequestMetrics
from backend.app.core.observability.tracing import (
    OTEL_AVAILABLE,
    SpanKind,
    Status,
    StatusCode,
    TracingState,
    current_trace_identifiers,
    propagate,
)


def route_group_for_path(path: str, api_prefix: str) -> str | None:
    """Map dynamic paths to low-cardinality route groups."""
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


class ObservabilityMiddleware:
    """Request-level logs, tracing, and metric summaries for API traffic only."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        logger: logging.Logger,
        metrics: RequestMetrics,
        tracing_state: TracingState,
        slow_request_threshold_ms: float,
        api_v1_prefix: str,
        tracer: Any | None = None,
    ) -> None:
        self.app = app
        self.logger = logger
        self.metrics = metrics
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.tracing_state = tracing_state
        self.api_v1_prefix = api_v1_prefix
        self.tracer = tracer

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        route_group = route_group_for_path(path, self.api_v1_prefix)
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
            trace_id, span_id = current_trace_identifiers()

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
