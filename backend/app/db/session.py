"""Database session helpers and lifecycle utilities."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import settings
from backend.app.db.base import Base

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Initialise database schema on startup."""

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""

    async with AsyncSessionFactory() as session:
        yield session
