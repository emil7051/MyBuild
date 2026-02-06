"""Custom middleware for security and request handling.

SEC-004: Request body size limits to prevent DoS via large payloads.
"""

from __future__ import annotations

from fastapi import status
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.core.config import settings


class RequestSizeLimitMiddleware:
    """Middleware to enforce maximum request body size (SEC-004).

    Enforces body size limits in two ways:
    1. Early rejection if Content-Length header exceeds the limit
    2. Streaming byte counter that aborts before app handlers execute if actual
       bytes exceed the limit (handles chunked transfers and forged headers)
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.max_size = settings.max_request_body_size

    @staticmethod
    def _payload_too_large_response(max_size: int) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": f"Request body too large. Max size: {max_size} bytes."},
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Early rejection if Content-Length header indicates oversized body
        content_length = Headers(scope=scope).get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_size:
                    response = self._payload_too_large_response(self.max_size)
                    await response(scope, receive, send)
                    return
            except ValueError:
                pass  # Invalid header, will be caught by streaming check

        # Buffer the request body while counting bytes so we can reject oversized
        # payloads before any route logic executes.
        body_parts: list[bytes] = []
        received_bytes = 0

        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            body = message.get("body", b"")
            if body:
                received_bytes += len(body)
                if received_bytes > self.max_size:
                    response = self._payload_too_large_response(self.max_size)
                    await response(scope, receive, send)
                    return
                body_parts.append(body)

            if not message.get("more_body", False):
                break

        buffered_body = b"".join(body_parts)
        body_sent = False

        async def replay_receive() -> Message:
            nonlocal body_sent
            if body_sent:
                return {"type": "http.request", "body": b"", "more_body": False}
            body_sent = True
            return {"type": "http.request", "body": buffered_body, "more_body": False}

        await self.app(scope, replay_receive, send)
