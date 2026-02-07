"""Database session helpers and lifecycle utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.db.base import Base  # noqa: F401 - needed for Alembic metadata

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
logger = logging.getLogger(__name__)


MIGRATION_SYNC_SCHEME_MAP: dict[str, str] = {
    "sqlite": "sqlite",
    "sqlite+aiosqlite": "sqlite",
    "sqlite+pysqlite": "sqlite",
    "postgres": "postgresql+psycopg2",
    "postgresql": "postgresql+psycopg2",
    "postgresql+asyncpg": "postgresql+psycopg2",
    "postgresql+psycopg2": "postgresql+psycopg2",
}


def _get_alembic_config() -> Config:
    """Get Alembic configuration pointing to our migrations."""
    # Find the backend directory (where alembic.ini lives)
    backend_dir = Path(__file__).parent.parent.parent
    alembic_ini = backend_dir / "alembic.ini"

    if not alembic_ini.exists():
        raise FileNotFoundError(
            f"Alembic configuration not found at {alembic_ini}. "
            "Ensure alembic.ini exists in the backend directory."
        )

    config = Config(str(alembic_ini))
    # Override script_location to absolute path for reliability
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    return config


def _to_sync_migration_url(db_url: str) -> str:
    """Map runtime DB URLs to Alembic-compatible sync-driver URLs."""
    parsed = urlsplit(db_url)
    sync_scheme = MIGRATION_SYNC_SCHEME_MAP.get(parsed.scheme)
    if sync_scheme is None:
        supported = ", ".join(sorted(MIGRATION_SYNC_SCHEME_MAP))
        raise ValueError(
            f"Unsupported database URL scheme '{parsed.scheme}' for migrations. "
            f"Supported schemes: {supported}."
        )
    if sync_scheme == "sqlite":
        # Preserve SQLite's triple-slash semantics for local paths.
        normalized = f"sqlite://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized = f"{normalized}?{parsed.query}"
        if parsed.fragment:
            normalized = f"{normalized}#{parsed.fragment}"
        return normalized
    return urlunsplit(
        (sync_scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment)
    )


async def init_db() -> None:
    """Initialise database schema on startup using Alembic migrations.

    This runs all pending migrations to bring the database to the latest
    schema version. For new databases, this creates all tables. For existing
    databases, it applies any pending migrations safely.

    Using Alembic instead of create_all() enables:
    - Safe schema evolution without data loss
    - Rollback capability for failed deployments
    - Audit trail of schema changes
    """
    if not settings.should_run_migrations:
        logger.info("Skipping migrations: RUN_MIGRATIONS is disabled.")
        return
    # Run migrations synchronously (Alembic doesn't have async support)
    # This is safe at startup before any async operations begin
    config = _get_alembic_config()

    sync_url = _to_sync_migration_url(settings.database_url)
    config.set_main_option("sqlalchemy.url", sync_url)

    # Run migrations to head (latest version)
    command.upgrade(config, "head")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""

    async with AsyncSessionFactory() as session:
        yield session


def run_migrations_offline(output_file: str | None = None) -> None:
    """Generate SQL migration script without connecting to the database.

    Useful for reviewing migrations before applying them or for
    generating scripts to run manually in production.

    Args:
        output_file: Optional path to write SQL output. If None, prints to stdout.
    """
    config = _get_alembic_config()
    if output_file:
        with open(output_file, "w", encoding="utf-8") as output_buffer:
            config.output_buffer = output_buffer
            command.upgrade(config, "head", sql=True)
        return
    command.upgrade(config, "head", sql=True)
