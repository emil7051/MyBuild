"""Alembic migration environment configuration.

Supports both offline (SQL generation) and online (direct execution) migrations.
Works with SQLite (development) and PostgreSQL (production).
Always uses sync drivers to avoid event loop conflicts when called from FastAPI.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from backend.app.core.config import settings
from backend.app.db.base import Base

# Import all models so they register with Base.metadata
from backend.app.db import models  # noqa: F401

# Alembic Config object, provides access to .ini values
config = context.config

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL, preferring config setting over app settings.

    When run via alembic CLI, the URL comes from alembic.ini or command line.
    When run programmatically, it may be set in config or fall back to app settings.
    """
    # First check if URL was set in config (e.g., by tests or CLI override)
    config_url = config.get_main_option("sqlalchemy.url")
    if config_url and not config_url.startswith("driver://"):
        url = config_url
    else:
        url = settings.database_url

    # Convert async driver to sync for offline migrations
    # aiosqlite -> sqlite, asyncpg -> postgresql+psycopg2
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite")
    if url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL script output rather than connecting to the database.
    Useful for reviewing migrations before applying them.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render as batch operations for SQLite ALTER TABLE support
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations using a provided connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Render as batch operations for SQLite ALTER TABLE support
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates a connection and runs migrations directly against the database.
    Always uses sync drivers to avoid asyncio.run() conflicts when called
    from within an existing event loop (e.g., FastAPI lifespan startup).
    """
    from sqlalchemy import create_engine

    # Always use sync URL - get_url() converts async drivers to sync
    sync_url = get_url()
    connectable = create_engine(sync_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
