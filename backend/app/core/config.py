"""Application configuration via environment variables."""

from functools import lru_cache
import os
from typing import List, Optional
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI service."""

    project_name: str = Field(default="TCO Web Platform API")
    version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")
    environment: str = Field(default="development")
    backend_cors_origins: List[AnyHttpUrl] | List[str] = Field(
        default_factory=lambda: ["http://localhost:5000", "http://127.0.0.1:5000"]
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./tco.db",
        description="SQLAlchemy-compatible database URL.",
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for session caching (omit to disable).",
    )
    session_ttl_seconds: int = Field(
        default=1800, ge=60, description="TTL for cached wizard sessions in Redis."
    )

    # Security settings (Phase 4 / SEC-004, SEC-007, SEC-008)
    max_request_body_size: int = Field(
        default=1_048_576,  # 1 MB
        ge=1024,
        description="Maximum request body size in bytes.",
    )
    trusted_proxies: List[str] = Field(
        default_factory=list,
        description=(
            "List of trusted proxy IPs or CIDRs. X-Forwarded-For header is only "
            "trusted when request comes from these addresses. Empty = trust no proxies."
        ),
    )
    rate_limit_sessions_per_minute: int = Field(
        default=30,
        ge=1,
        description="Max session create/update requests per IP per minute.",
    )
    rate_limit_analytics_per_minute: int = Field(
        default=10,
        ge=1,
        description="Max analytics requests per IP per minute.",
    )
    rate_limit_vehicles_per_minute: int = Field(
        default=60,
        ge=1,
        description="Max vehicle catalog requests per IP per minute.",
    )
    analytics_api_key: Optional[str] = Field(
        default=None,
        description="API key for analytics endpoint. If None, unrestricted.",
    )

    @field_validator("backend_cors_origins", "trusted_proxies", mode="before")
    @classmethod
    def _split_comma_list(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("backend_cors_origins")
    @classmethod
    def _validate_cors_origins(cls, value):
        if "*" in value:
            raise ValueError(
                "BACKEND_CORS_ORIGINS cannot include '*' when credentials are enabled."
            )
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value):
        """Convert standard postgres URLs to async postgresql+asyncpg URLs."""
        if not isinstance(value, str):
            return value

        # Only process postgres/postgresql URLs
        if not (value.startswith("postgres://") or value.startswith("postgresql://")):
            return value

        # Parse the URL
        parts = urlsplit(value)

        # Convert scheme to async driver
        scheme = "postgresql+asyncpg"

        # Parse query parameters
        query_params = parse_qs(parts.query, keep_blank_values=True)

        # Handle SSL mode for asyncpg compatibility
        # asyncpg doesn't support sslmode parameter. Remove it from the
        # connection string. asyncpg will handle SSL automatically with
        # Neon's connection string.
        if "sslmode" in query_params:
            query_params.pop("sslmode")

        # Also remove any ssl parameter if present
        if "ssl" in query_params:
            query_params.pop("ssl")

        # Rebuild query string
        new_query = urlencode(query_params, doseq=True) if query_params else ""

        # Reconstruct URL
        return urlunsplit((scheme, parts.netloc, parts.path, new_query, parts.fragment))

    # Only load .env in development to avoid overriding production secrets.
    _env_file = (
        "backend/.env"
        if os.getenv("ENVIRONMENT", "development") == "development"
        else None
    )
    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()
