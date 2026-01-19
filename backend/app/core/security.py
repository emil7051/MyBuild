"""Security utilities for session access control and rate limiting.

SEC-005: Session access-control secret generation and verification.
SEC-008: Rate limiting configuration for session and analytics endpoints.
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network
import secrets
from typing import Optional

import bcrypt
from fastapi import HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.config import settings


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
    direct_ip = get_remote_address(request)

    # Only trust X-Forwarded-For if request came from a trusted proxy
    if _is_trusted_proxy(direct_ip):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()

    return direct_ip


# Rate limiter instance using client IP
limiter = Limiter(key_func=get_client_ip)


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
    except Exception:
        return False


def get_session_secret_header(request: Request) -> Optional[str]:
    """Extract session secret from request header.

    The secret can be provided via the X-Session-Secret header.
    """
    return request.headers.get("X-Session-Secret")


def verify_analytics_api_key(request: Request) -> None:
    """Verify the analytics API key if configured (SEC-007).

    Raises HTTPException 401 if API key is required but missing/invalid.
    """
    if settings.analytics_api_key is None:
        # No API key configured, endpoint is unrestricted
        return

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
