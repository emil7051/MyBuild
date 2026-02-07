"""Unit tests for API router helper behavior."""

from __future__ import annotations

import pytest
from fastapi import Request, Response

from backend.app.api import router
from backend.app.core import config


def _build_request_with_session_secret(session_secret: str | None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if session_secret is not None:
        cookie_name = config.settings.session_secret_cookie_name
        cookie_header = f"{cookie_name}={session_secret}".encode("latin-1")
        headers.append((b"cookie", cookie_header))

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/sessions/test",
        "query_string": b"",
        "headers": headers,
    }
    return Request(scope)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("session_secret", "expect_cookie_refresh"),
    [("test-secret", True), (None, False)],
)
async def test_run_with_session_secret_shared_lifecycle(
    session_secret: str | None, expect_cookie_refresh: bool
) -> None:
    request = _build_request_with_session_secret(session_secret)
    response = Response()
    seen_secrets: list[str | None] = []

    async def _operation(resolved_secret: str | None) -> dict[str, bool]:
        seen_secrets.append(resolved_secret)
        return {"ok": True}

    result = await router._run_with_session_secret(request, response, _operation)

    assert result == {"ok": True}
    assert seen_secrets == [session_secret]

    set_cookie_header = response.headers.get("set-cookie")
    if expect_cookie_refresh:
        assert set_cookie_header is not None
        cookie_name = config.settings.session_secret_cookie_name
        assert f"{cookie_name}={session_secret}" in set_cookie_header
    else:
        assert set_cookie_header is None
