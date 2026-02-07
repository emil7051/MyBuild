"""Unit tests for modularized observability components."""

from __future__ import annotations

import json
import logging

from backend.app.core.observability import (
    AlertDispatcher,
    RequestAlertPolicy,
    RequestMetrics,
    StructuredJSONFormatter,
    create_observability_runtime,
)
from backend.app.core.observability.middleware import route_group_for_path
from backend.app.core.observability.tracing import parse_otlp_headers


def test_structured_json_formatter_normalizes_extras() -> None:
    sentinel = object()
    record = logging.makeLogRecord(
        {
            "name": "backend.observability",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "hello",
            "args": (),
            "payload": {"nested": [1, sentinel]},
        }
    )

    rendered = StructuredJSONFormatter().format(record)
    payload = json.loads(rendered)
    assert payload["message"] == "hello"
    assert payload["payload"]["nested"][0] == 1
    assert isinstance(payload["payload"]["nested"][1], str)


def test_parse_otlp_headers_ignores_invalid_entries() -> None:
    parsed = parse_otlp_headers("api-key=abc, malformed, empty=,team = backend")
    assert parsed == {"api-key": "abc", "team": "backend"}


def test_alert_dispatcher_no_webhook_is_noop() -> None:
    dispatcher = AlertDispatcher(
        logger=logging.getLogger("tests.observability.alerts"),
        webhook_url=None,
    )
    dispatcher.dispatch({"event": "http.alert"})


def test_request_metrics_emits_alert_payload() -> None:
    captured_records: list[logging.LogRecord] = []
    dispatched_payloads: list[dict[str, object]] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_records.append(record)

    logger = logging.getLogger("tests.observability.metrics")
    logger.handlers.clear()
    logger.addHandler(_CaptureHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False

    class _Dispatcher(AlertDispatcher):
        def __init__(self) -> None:
            super().__init__(logger=logger, webhook_url=None)

        def dispatch(self, payload: dict[str, object]) -> None:
            dispatched_payloads.append(payload)

    metrics = RequestMetrics(
        logger=logger,
        emit_interval_seconds=10,
        alert_policy=RequestAlertPolicy(
            min_requests=1,
            error_rate_threshold=0.5,
            avg_duration_ms_threshold=999_999,
            cooldown_seconds=60,
        ),
        alert_dispatcher=_Dispatcher(),
    )
    metrics._next_emit_at = 0.0

    metrics.record("sessions", 500, 12.0)

    alert_records = [
        record
        for record in captured_records
        if getattr(record, "event", "") == "http.alert"
    ]
    assert alert_records
    assert dispatched_payloads
    assert dispatched_payloads[0]["event"] == "http.alert"


def test_route_group_for_path_uses_api_prefix() -> None:
    assert route_group_for_path("/api/v1/sessions/abc", "/api/v1") == "sessions"
    assert route_group_for_path("/api/v1/health", "/api/v1") == "health"
    assert route_group_for_path("/status", "/api/v1") is None


def test_create_observability_runtime_wires_components() -> None:
    runtime = create_observability_runtime()
    assert runtime.logger.name == "backend.observability"
    assert runtime.request_metrics.alert_dispatcher is runtime.alert_dispatcher
    assert runtime.tracing_state.configured
