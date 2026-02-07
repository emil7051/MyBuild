"""Tests for database session helpers."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from backend.app.db import session as db_session


class DummyAlembicConfig:
    """Minimal Alembic config test double."""

    def __init__(self) -> None:
        self.main_options: dict[str, str] = {}
        self.output_buffer = None

    def set_main_option(self, key: str, value: str) -> None:
        self.main_options[key] = value


def test_get_alembic_config_sets_absolute_script_location() -> None:
    config = db_session._get_alembic_config()
    script_location = Path(config.get_main_option("script_location"))

    assert script_location.is_absolute()
    assert script_location.name == "alembic"
    assert script_location.parent.name == "backend"


def test_get_alembic_config_raises_when_ini_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_module_path = tmp_path / "backend" / "app" / "db" / "session.py"
    fake_module_path.parent.mkdir(parents=True, exist_ok=True)
    fake_module_path.write_text("# synthetic module path for test", encoding="utf-8")

    monkeypatch.setattr(db_session, "__file__", str(fake_module_path))

    with pytest.raises(FileNotFoundError, match="alembic.ini"):
        db_session._get_alembic_config()


def test_init_db_uses_sqlite_sync_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    config = DummyAlembicConfig()
    calls: list[tuple[DummyAlembicConfig, str]] = []

    def _fake_upgrade(passed_config: DummyAlembicConfig, revision: str) -> None:
        calls.append((passed_config, revision))

    monkeypatch.setattr(db_session, "_get_alembic_config", lambda: config)
    monkeypatch.setattr(db_session.command, "upgrade", _fake_upgrade)
    monkeypatch.setattr(db_session.settings, "run_migrations", True, raising=False)
    monkeypatch.setattr(
        db_session.settings,
        "database_url",
        "sqlite+aiosqlite:///./test.db",
        raising=False,
    )

    asyncio.run(db_session.init_db())

    assert config.main_options["sqlalchemy.url"] == "sqlite:///./test.db"
    assert calls == [(config, "head")]


def test_init_db_uses_postgres_sync_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    config = DummyAlembicConfig()
    calls: list[tuple[DummyAlembicConfig, str]] = []

    def _fake_upgrade(passed_config: DummyAlembicConfig, revision: str) -> None:
        calls.append((passed_config, revision))

    monkeypatch.setattr(db_session, "_get_alembic_config", lambda: config)
    monkeypatch.setattr(db_session.command, "upgrade", _fake_upgrade)
    monkeypatch.setattr(db_session.settings, "run_migrations", True, raising=False)
    monkeypatch.setattr(
        db_session.settings,
        "database_url",
        "postgresql+asyncpg://user:pass@localhost:5432/app",
        raising=False,
    )

    asyncio.run(db_session.init_db())

    assert (
        config.main_options["sqlalchemy.url"]
        == "postgresql+psycopg2://user:pass@localhost:5432/app"
    )
    assert calls == [(config, "head")]


def test_get_db_session_yields_factory_session(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_session = object()

    class DummySessionFactory:
        def __init__(self) -> None:
            self.entered = False
            self.exited = False

        def __call__(self) -> DummySessionFactory:
            return self

        async def __aenter__(self):
            self.entered = True
            return expected_session

        async def __aexit__(self, *_args) -> bool:
            self.exited = True
            return False

    factory = DummySessionFactory()
    monkeypatch.setattr(db_session, "AsyncSessionFactory", factory)

    async def _read_one():
        generator = db_session.get_db_session()
        yielded_session = await anext(generator)
        await generator.aclose()
        return yielded_session

    yielded = asyncio.run(_read_one())

    assert yielded is expected_session
    assert factory.entered is True
    assert factory.exited is True


def test_run_migrations_offline_writes_output_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = DummyAlembicConfig()
    calls: list[tuple[DummyAlembicConfig, str, bool]] = []

    def _fake_upgrade(
        passed_config: DummyAlembicConfig, revision: str, sql: bool = False
    ) -> None:
        calls.append((passed_config, revision, sql))
        if passed_config.output_buffer is not None:
            passed_config.output_buffer.write("-- migration SQL")

    monkeypatch.setattr(db_session, "_get_alembic_config", lambda: config)
    monkeypatch.setattr(db_session.command, "upgrade", _fake_upgrade)

    output_file = tmp_path / "migration.sql"
    db_session.run_migrations_offline(str(output_file))

    assert output_file.read_text(encoding="utf-8") == "-- migration SQL"
    assert calls == [(config, "head", True)]


def test_run_migrations_offline_without_output_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = DummyAlembicConfig()
    calls: list[tuple[DummyAlembicConfig, str, bool]] = []

    def _fake_upgrade(
        passed_config: DummyAlembicConfig, revision: str, sql: bool = False
    ) -> None:
        calls.append((passed_config, revision, sql))

    monkeypatch.setattr(db_session, "_get_alembic_config", lambda: config)
    monkeypatch.setattr(db_session.command, "upgrade", _fake_upgrade)

    db_session.run_migrations_offline()

    assert calls == [(config, "head", True)]
    assert config.output_buffer is None
