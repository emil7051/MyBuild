"""Tests for configuration normalization logic."""

from __future__ import annotations

import pytest
from pydantic_settings import SettingsConfigDict

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


def test_reject_invalid_tracing_sample_rate() -> None:
    with pytest.raises(ValueError, match="observability_tracing_sample_rate"):
        Settings(observability_tracing_sample_rate=1.5)


def test_reject_invalid_alert_error_rate_threshold() -> None:
    with pytest.raises(ValueError, match="observability_alert_error_rate_threshold"):
        Settings(observability_alert_error_rate_threshold=-0.1)


def test_ignore_unknown_dotenv_keys(tmp_path) -> None:
    env_file = tmp_path / "deployment.env"
    env_file.write_text("UNKNOWN_DEPLOYMENT_FLAG=true\n", encoding="utf-8")

    config = dict(Settings.model_config)
    config["env_file"] = str(env_file)

    class TestSettings(Settings):
        model_config = SettingsConfigDict(**config)

    TestSettings()
