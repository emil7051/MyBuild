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
    rate_limit_redis_url: Optional[str] = Field(
        default=None,
        description=(
            "Redis connection string for slowapi rate limit storage. "
            "Defaults to REDIS_URL outside development."
        ),
    )
    session_ttl_seconds: int = Field(
        default=1800, ge=60, description="TTL for cached wizard sessions in Redis."
    )
    session_secret_cookie_name: str = Field(
        default="tco_session_secret",
        description="Cookie name for the HttpOnly session secret.",
    )
    session_secret_cookie_max_age_days: int = Field(
        default=30,
        ge=1,
        description="Max age (days) for the session secret cookie.",
    )
    session_secret_cookie_samesite: str = Field(
        default="lax",
        description="SameSite policy for the session secret cookie.",
    )
    session_secret_cookie_secure: Optional[bool] = Field(
        default=None,
        description=(
            "Whether the session secret cookie should be Secure. "
            "Defaults to True outside development."
        ),
    )

    # Security and traffic-control settings.
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
    observability_tracing_enabled: bool = Field(
        default=True,
        description="Enable sampled distributed tracing for API requests.",
    )
    observability_tracing_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Trace sampling ratio (0.0-1.0) for new root requests.",
    )
    observability_tracing_service_name: str = Field(
        default="tco-web-platform-api",
        description="Service name attached to emitted trace resources.",
    )
    observability_tracing_otlp_endpoint: Optional[str] = Field(
        default=None,
        description=(
            "Optional OTLP/HTTP endpoint for traces. "
            "If omitted, traces are written to stdout."
        ),
    )
    observability_tracing_otlp_headers: Optional[str] = Field(
        default=None,
        description=("Optional comma-separated OTLP headers in key=value format."),
    )
    observability_metrics_emit_interval_seconds: int = Field(
        default=60,
        ge=10,
        description="Seconds between in-memory HTTP metric summary log windows.",
    )
    observability_slow_request_threshold_ms: float = Field(
        default=750.0,
        ge=1.0,
        description="Request duration threshold (ms) for slow-request log entries.",
    )
    observability_alert_min_requests: int = Field(
        default=20,
        ge=1,
        description="Minimum requests in a metrics window before alerting can trigger.",
    )
    observability_alert_error_rate_threshold: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Error-rate threshold for request-window alert events.",
    )
    observability_alert_avg_duration_ms_threshold: float = Field(
        default=1500.0,
        ge=1.0,
        description="Average duration threshold (ms) for request-window alert events.",
    )
    observability_alert_cooldown_seconds: int = Field(
        default=300,
        ge=10,
        description="Cooldown window between repeated alert emissions.",
    )
    observability_alert_webhook_url: Optional[str] = Field(
        default=None,
        description="Optional webhook URL for forwarding structured alert payloads.",
    )
    observability_alert_webhook_timeout_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=10.0,
        description="Webhook timeout (seconds) for alert dispatch.",
    )
    analytics_api_key: Optional[str] = Field(
        default=None,
        description="API key for analytics endpoint. If None, endpoint is disabled.",
    )
    run_migrations: Optional[bool] = Field(
        default=None,
        description=(
            "Run Alembic migrations on app startup. "
            "Defaults to True in development and False otherwise."
        ),
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

    @property
    def should_run_migrations(self) -> bool:
        if self.run_migrations is not None:
            return self.run_migrations
        return self.environment == "development"

    @property
    def session_secret_cookie_secure_effective(self) -> bool:
        if self.session_secret_cookie_secure is not None:
            return self.session_secret_cookie_secure
        return self.environment != "development"

    # Only load a local dotenv file in development.
    # Deployment platforms often inject additional env keys that are not part of
    # this Settings model; ignore those extras so startup remains resilient.
    _env_file_path = "backend/.env"
    _env_file = (
        _env_file_path
        if os.getenv("ENVIRONMENT", "development") == "development"
        and os.path.exists(_env_file_path)
        else None
    )
    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()
