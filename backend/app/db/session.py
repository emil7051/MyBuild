"""Database session helpers and lifecycle utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import AsyncGenerator

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.db.base import Base  # noqa: F401 - needed for Alembic metadata

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
logger = logging.getLogger(__name__)


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

    # Check if we're using SQLite (development) or PostgreSQL (production)
    db_url = settings.database_url

    if db_url.startswith("sqlite"):
        # For SQLite, we need sync driver - convert URL
        sync_url = db_url.replace("sqlite+aiosqlite", "sqlite")
        config.set_main_option("sqlalchemy.url", sync_url)
    else:
        # For PostgreSQL, convert async to sync driver
        sync_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
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
