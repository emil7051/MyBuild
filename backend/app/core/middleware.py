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

    Rejects requests with Content-Length exceeding the configured limit
    with a 413 Payload Too Large response.
    """

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > settings.max_request_body_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": (
                                f"Request body too large. "
                                f"Max size: {settings.max_request_body_size} bytes."
                            )
                        },
                    )
            except ValueError:
                # Invalid Content-Length header, let it pass through
                # and fail at a later stage if necessary
                pass

        response = await call_next(request)
        return response
