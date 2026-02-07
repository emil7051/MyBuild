"""Custom middleware for security and request handling.

See `docs/security-requirements.md` for policy details.
"""

from __future__ import annotations

from fastapi import status
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.core.config import settings


class RequestSizeLimitMiddleware:
    """Middleware to enforce maximum request body size.

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

        # Buffer request chunks while counting bytes so we can reject oversized
        # payloads before any route logic executes.
        buffered_chunks: list[bytes] = []
        received_bytes = 0

        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return

            if message["type"] != "http.request":
                continue

            body = message.get("body", b"")
            received_bytes += len(body)
            if received_bytes > self.max_size:
                response = self._payload_too_large_response(self.max_size)
                await response(scope, receive, send)
                return
            if body:
                buffered_chunks.append(body)

            if not message.get("more_body", False):
                break

        chunk_index = 0

        async def replay_receive() -> Message:
            nonlocal chunk_index
            if chunk_index >= len(buffered_chunks):
                return {"type": "http.request", "body": b"", "more_body": False}
            body = buffered_chunks[chunk_index]
            chunk_index += 1
            return {
                "type": "http.request",
                "body": body,
                "more_body": chunk_index < len(buffered_chunks),
            }

        await self.app(scope, replay_receive, send)
