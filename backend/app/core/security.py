"""Security utilities for rate limiting and optional access control helpers.

See `docs/security-requirements.md` for policy details.
"""

from __future__ import annotations

import hashlib
from ipaddress import ip_address, ip_network
import logging
import secrets

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    _SLOWAPI_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - optional dependency at runtime
    Limiter = None
    get_remote_address = None
    _SLOWAPI_AVAILABLE = False

from backend.app.core.config import settings  # noqa: E402

_SESSION_SECRET_SHA256_PREFIX = "sha256$"


class RateLimiterConfigurationError(RuntimeError):
    """Raised when rate-limiter safety requirements are not met."""


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


def _get_rate_limit_storage_uri() -> str | None:
    if settings.rate_limit_redis_url:
        return settings.rate_limit_redis_url
    if settings.environment != "development":
        return settings.redis_url
    return None


def validate_rate_limiter_configuration() -> None:
    """Enforce non-development rate-limit safety requirements.

    In non-development environments, startup must fail unless the application can
    build a real limiter with shared storage. This can be bypassed temporarily via
    the ALLOW_INSECURE_RATE_LIMITER emergency override.
    """
    if settings.environment == "development":
        return

    if settings.allow_insecure_rate_limiter:
        logger.warning(
            "SECURITY WARNING: ALLOW_INSECURE_RATE_LIMITER=true in %s. "
            "Rate limiting may run in a degraded mode.",
            settings.environment,
        )
        return

    if not _SLOWAPI_AVAILABLE:
        raise RateLimiterConfigurationError(
            "slowapi is required outside development. Install slowapi or set "
            "ALLOW_INSECURE_RATE_LIMITER=true for an emergency override."
        )

    storage_uri = _get_rate_limit_storage_uri()
    if not storage_uri:
        raise RateLimiterConfigurationError(
            "Shared rate-limit storage is required outside development. Set "
            "RATE_LIMIT_REDIS_URL (or REDIS_URL) or use "
            "ALLOW_INSECURE_RATE_LIMITER=true for an emergency override."
        )


def _build_limiter():
    if _SLOWAPI_AVAILABLE:
        storage_uri = _get_rate_limit_storage_uri()
        if storage_uri:
            return Limiter(key_func=get_client_ip, storage_uri=storage_uri)
        logger.warning(
            "SECURITY WARNING: slowapi storage not configured; "
            "rate limiting will be per-process only."
        )
        return Limiter(key_func=get_client_ip)

    logger.warning(
        "SECURITY WARNING: slowapi not available. Rate limiting is DISABLED. "
        "Install slowapi to enable rate limiting: pip install slowapi"
    )
    return _NoopLimiter()


# Rate limiter instance using client IP (no-op if slowapi missing)
limiter = _build_limiter()


def generate_session_secret() -> str:
    """Generate a cryptographically secure session access secret.

    Returns a URL-safe token suitable for use as a session secret.
    The secret is 32 bytes (256 bits) of random data, encoded as base64.
    """
    return secrets.token_urlsafe(32)


def hash_secret(secret: str) -> str:
    """Hash a session secret using SHA-256.

    Args:
        secret: The plaintext session secret to hash.

    Returns:
        A prefixed SHA-256 hash of the secret.
    """
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return f"{_SESSION_SECRET_SHA256_PREFIX}{digest}"


def verify_secret(secret: str, hashed: str) -> bool:
    """Verify a session secret against its stored hash.

    Args:
        secret: The plaintext session secret to verify.
        hashed: The stored hash to verify against.

    Returns:
        True if the secret matches the hash, False otherwise.
    """
    try:
        if hashed.startswith(_SESSION_SECRET_SHA256_PREFIX):
            expected_digest = hashed.removeprefix(_SESSION_SECRET_SHA256_PREFIX)
            provided_digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
            return secrets.compare_digest(provided_digest, expected_digest)

        logger.warning("Unsupported session secret hash format.")
        return False
    except (ValueError, TypeError) as exc:
        logger.warning("Invalid session secret hash: %s", exc)
        return False
    except Exception:
        logger.exception("Unexpected error while verifying session secret.")
        raise


def verify_session_secret(provided: str | None, hashed: str | None) -> None:
    """Verify session secret cookie against stored hash.

    Raises HTTPException if the secret is required and missing/invalid.
    """
    if not hashed:
        return

    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session secret required. Missing session secret cookie.",
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
    """Verify the analytics API key.

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
