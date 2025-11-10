"""Application configuration via environment variables."""

from functools import lru_cache
from typing import List, Optional
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI service."""

    project_name: str = Field(default="TCO Web Platform API")
    version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")
    environment: str = Field(default="development")
    backend_cors_origins: List[AnyHttpUrl] | List[str] = Field(
        default_factory=lambda: ["http://localhost:5000"]
    )
    cache_results: bool = Field(
        default=True, description="Toggle for caching calculation runs in memory."
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./tco.db",
        description="SQLAlchemy-compatible database URL.",
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for session caching.",
    )
    session_ttl_seconds: int = Field(
        default=1800, ge=60, description="TTL for cached wizard sessions in Redis."
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
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
        
        # Parse query parameters and remove SSL-related ones
        query_params = parse_qs(parts.query, keep_blank_values=True)
        # Remove sslmode and ssl parameters
        query_params.pop("sslmode", None)
        query_params.pop("ssl", None)
        
        # Rebuild query string
        new_query = urlencode(query_params, doseq=True) if query_params else ""
        
        # Reconstruct URL
        return urlunsplit((scheme, parts.netloc, parts.path, new_query, parts.fragment))

    class Config:
        env_file = "backend/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()


settings = get_settings()
