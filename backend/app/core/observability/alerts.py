"""Alerting primitives for observability signals."""

from __future__ import annotations

from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import logging
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


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
