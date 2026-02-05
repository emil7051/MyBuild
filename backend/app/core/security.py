"""Security utilities for rate limiting and optional access control helpers.

SEC-008: Rate limiting configuration for session and analytics endpoints.
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network
import logging
import secrets

import bcrypt
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    _SLOWAPI_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - optional dependency at runtime
    Limiter = None  # type: ignore[assignment]
    get_remote_address = None  # type: ignore[assignment]
    _SLOWAPI_AVAILABLE = False

from backend.app.core.config import settings  # noqa: E402


def _is_trusted_proxy(direct_ip: str) -> bool:
    """Check if the direct connection IP is from a trusted proxy."""
    if not settings.trusted_proxies:
        return False

    try:
        addr = ip_address(direct_ip)
        for proxy in settings.trusted_proxies:
            try:
                if addr in ip_network(proxy, strict=False):
                    return True
            except ValueError:
                # Invalid CIDR in config, skip it
                continue
    except ValueError:
        # Invalid IP address format
        return False

    return False


def get_client_ip(request: Request) -> str:
    """Get client IP address, respecting X-Forwarded-For only from trusted proxies.

    X-Forwarded-For is only trusted when the direct connection comes from an IP
    in the trusted_proxies list. This prevents clients from spoofing the header
    to bypass rate limits.
    """
    if get_remote_address:
        direct_ip = get_remote_address(request)
    else:
        direct_ip = request.client.host if request.client else "unknown"

    # Only trust X-Forwarded-For if request came from a trusted proxy
    if _is_trusted_proxy(direct_ip):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()

    return direct_ip


class _NoopLimiter:
    """Fallback limiter when slowapi is unavailable."""

    @staticmethod
    def limit(_limit: str):
        def decorator(func):
            return func

        return decorator


# Rate limiter instance using client IP (no-op if slowapi missing)
if _SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_client_ip)
else:
    logger.warning(
        "SECURITY WARNING: slowapi not available. Rate limiting is DISABLED. "
        "Install slowapi to enable rate limiting: pip install slowapi"
    )
    limiter = _NoopLimiter()


def generate_session_secret() -> str:
    """Generate a cryptographically secure session access secret.

    Returns a URL-safe token suitable for use as a session secret.
    The secret is 32 bytes (256 bits) of random data, encoded as base64.
    """
    return secrets.token_urlsafe(32)


def hash_secret(secret: str) -> str:
    """Hash a session secret using bcrypt.

    Args:
        secret: The plaintext session secret to hash.

    Returns:
        The bcrypt hash of the secret (60 characters).
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(secret.encode("utf-8"), salt).decode("utf-8")


def verify_secret(secret: str, hashed: str) -> bool:
    """Verify a session secret against its stored hash.

    Args:
        secret: The plaintext session secret to verify.
        hashed: The bcrypt hash to verify against.

    Returns:
        True if the secret matches the hash, False otherwise.
    """
    try:
        return bcrypt.checkpw(secret.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        logger.warning("Invalid session secret hash: %s", exc)
        return False
    except Exception:
        logger.exception("Unexpected error while verifying session secret.")
        raise


def verify_session_secret(provided: str | None, hashed: str | None) -> None:
    """Verify session secret header against stored hash.

    Raises HTTPException if the secret is required and missing/invalid.
    """
    if not hashed:
        return

    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session secret required. Provide X-Session-Secret header.",
        )

    try:
        is_valid = verify_secret(provided, hashed)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session secret verification failed.",
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid session secret.",
        )


def verify_analytics_api_key(request: Request) -> None:
    """Verify the analytics API key (SEC-007).

    Raises HTTPException 403 if the endpoint is disabled (no key configured),
    or 401 if the key is missing/invalid.
    """
    if settings.analytics_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics API key is not configured. Endpoint disabled.",
        )

    provided_key = request.headers.get("X-Analytics-Key")
    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Analytics API key required. Provide X-Analytics-Key header.",
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(provided_key, settings.analytics_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid analytics API key.",
        )


def get_rate_limit_sessions() -> str:
    """Get rate limit string for session endpoints."""
    return f"{settings.rate_limit_sessions_per_minute}/minute"


def get_rate_limit_analytics() -> str:
    """Get rate limit string for analytics endpoint."""
    return f"{settings.rate_limit_analytics_per_minute}/minute"


def get_rate_limit_vehicles() -> str:
    """Get rate limit string for vehicle catalog endpoints."""
    return f"{settings.rate_limit_vehicles_per_minute}/minute"
