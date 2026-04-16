"""Tests for configuration normalization logic."""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict
import pytest

from backend.app.core.config import Settings


def test_split_cors_origins() -> None:
    settings = Settings(backend_cors_origins="http://a.com, http://b.com")
    assert settings.backend_cors_origins == ["http://a.com", "http://b.com"]


def test_reject_wildcard_cors_origins() -> None:
    with pytest.raises(ValueError, match="BACKEND_CORS_ORIGINS"):
        Settings(backend_cors_origins="*")


def test_normalize_database_url_postgres() -> None:
    settings = Settings(
        database_url="postgres://user:pass@localhost:5432/app?sslmode=require&ssl=true"
    )
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert "sslmode=" not in settings.database_url
    assert "ssl=" not in settings.database_url


def test_normalize_database_url_non_postgres() -> None:
    url = "sqlite+aiosqlite:///./local.db"
    settings = Settings(database_url=url)
    assert settings.database_url == url


def test_require_explicit_service_urls_outside_development() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL must be explicitly configured"):
        Settings(environment="production")


def test_reject_default_redis_url_outside_development() -> None:
    with pytest.raises(ValueError, match="REDIS_URL must be explicitly configured"):
        Settings(
            environment="staging",
            database_url="postgresql+asyncpg://user:pass@localhost:5432/app",
            redis_url="redis://localhost:6379/0",
        )


def test_allow_explicit_service_urls_outside_development() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/app",
        redis_url="redis://redis.internal:6379/2",
    )
    assert settings.environment == "production"
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.redis_url == "redis://redis.internal:6379/2"


def test_reject_invalid_tracing_sample_rate() -> None:
    with pytest.raises(ValueError, match="observability_tracing_sample_rate"):
        Settings(observability_tracing_sample_rate=1.5)


def test_reject_invalid_alert_error_rate_threshold() -> None:
    with pytest.raises(ValueError, match="observability_alert_error_rate_threshold"):
        Settings(observability_alert_error_rate_threshold=-0.1)


def test_accept_http_observability_alert_webhook_url() -> None:
    settings = Settings(
        observability_alert_webhook_url="https://alerts.example.com/hook"
    )
    assert settings.observability_alert_webhook_url == "https://alerts.example.com/hook"


def test_reject_non_http_observability_alert_webhook_url() -> None:
    with pytest.raises(ValueError, match="OBSERVABILITY_ALERT_WEBHOOK_URL"):
        Settings(observability_alert_webhook_url="file:///tmp/alert-hook")


def test_ignore_unknown_dotenv_keys(tmp_path) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("UNKNOWN_DEPLOYMENT_FLAG=true\n", encoding="utf-8")

    config = dict(Settings.model_config)
    config["env_file"] = str(env_file)

    class TestSettings(Settings):
        model_config = SettingsConfigDict(**config)

    TestSettings()
