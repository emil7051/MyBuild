"""Custom middleware for security and request handling.

SEC-004: Request body size limits to prevent DoS via large payloads.
"""

from __future__ import annotations

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.app.core.config import settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce maximum request body size (SEC-004).

    Enforces body size limits in two ways:
    1. Early rejection if Content-Length header exceeds the limit
    2. Streaming byte counter that aborts if actual bytes exceed the limit
       (handles chunked transfers and forged Content-Length headers)
    """

    async def dispatch(self, request: Request, call_next):
        max_size = settings.max_request_body_size

        # Early rejection if Content-Length header indicates oversized body
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": (
                                f"Request body too large. "
                                f"Max size: {max_size} bytes."
                            )
                        },
                    )
            except ValueError:
                pass  # Invalid header, will be caught by streaming check

        # Wrap receive to count actual bytes (handles chunked/missing headers)
        received_bytes = 0
        original_receive = request.receive
        size_exceeded = False

        async def limited_receive():
            nonlocal received_bytes, size_exceeded

            message = await original_receive()

            if message["type"] == "http.request":
                body = message.get("body", b"")
                received_bytes += len(body)

                if received_bytes > max_size:
                    size_exceeded = True
                    # Return empty body to stop processing
                    return {"type": "http.request", "body": b"", "more_body": False}

            return message

        # Replace the receive function with our limited version
        request._receive = limited_receive

        # Process the request
        response = await call_next(request)

        # If size was exceeded during body reading, return 413
        if size_exceeded:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "detail": (
                        f"Request body too large. " f"Max size: {max_size} bytes."
                    )
                },
            )

        return response
