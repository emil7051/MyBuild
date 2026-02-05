"""
Pytest configuration file.
Adds project root to Python path for test imports.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def pytest_configure() -> None:
    """Ensure the project root is available on sys.path for tests."""

    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


@pytest.fixture()
def anyio_backend() -> str:
    """Restrict anyio tests to asyncio to avoid optional trio dependency."""

    return "asyncio"


async def _create_schema(engine) -> None:
    from backend.app.db.base import Base

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def disable_redis_cache(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Disable Redis usage during tests to keep runs deterministic."""

    if request.node.get_closest_marker("enable_redis_cache"):
        return

    import backend.app.core.cache as cache_module
    import backend.app.services.sessions as sessions_module

    async def _noop_cache(*_args, **_kwargs) -> None:
        return None

    async def _noop_get(*_args, **_kwargs):
        return None

    async def _noop_client():
        return None

    monkeypatch.setattr(cache_module, "_redis_client", None, raising=False)
    monkeypatch.setattr(cache_module, "_next_retry_at", 0.0, raising=False)
    monkeypatch.setattr(cache_module, "_get_redis_client", _noop_client, raising=False)
    monkeypatch.setattr(cache_module.settings, "redis_url", None, raising=False)
    monkeypatch.setattr(sessions_module, "cache_session", _noop_cache)
    monkeypatch.setattr(sessions_module, "get_cached_session", _noop_get)


@pytest.fixture()
def async_engine(tmp_path: Path):
    """Create an isolated async engine backed by a temp sqlite database."""

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db", future=True)
    asyncio.run(_create_schema(engine))
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture()
def async_session_factory(
    async_engine,
) -> async_sessionmaker[AsyncSession]:
    """Return a sessionmaker bound to the test engine."""

    return async_sessionmaker(async_engine, expire_on_commit=False)


@pytest.fixture()
def app(async_session_factory: async_sessionmaker[AsyncSession], monkeypatch):
    """FastAPI app with the database dependency overridden for tests."""

    from backend.app.db.session import get_db_session
    import backend.app.main as main_module
    from backend.app.main import create_app

    async def _override_get_db_session():
        async with async_session_factory() as session:
            yield session

    async def _noop_init_db() -> None:
        return None

    monkeypatch.setattr(main_module, "init_db", _noop_init_db)

    application = create_app()
    application.dependency_overrides[get_db_session] = _override_get_db_session
    return application


@pytest.fixture()
async def client(app) -> httpx.AsyncClient:
    """Async test client for API tests."""

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        yield async_client
