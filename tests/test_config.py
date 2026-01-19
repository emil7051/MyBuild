"""Tests for configuration normalization logic."""

from __future__ import annotations

from backend.app.core.config import Settings


def test_split_cors_origins() -> None:
    settings = Settings(backend_cors_origins="http://a.com, http://b.com")
    assert settings.backend_cors_origins == ["http://a.com", "http://b.com"]


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
