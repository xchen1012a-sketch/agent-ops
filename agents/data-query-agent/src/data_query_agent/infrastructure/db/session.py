"""Async engine and session factory managed across the application lifecycle."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from data_query_agent.core.config import Settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db_engine(settings: Settings) -> None:
    """Create the async engine and session factory at app startup."""
    global _engine, _session_factory
    _engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_recycle=settings.database_pool_recycle_seconds,
        pool_pre_ping=True,
        future=True,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )


async def close_db_engine() -> None:
    """Dispose the engine at app shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def is_engine_ready() -> bool:
    """True when the engine and session factory are initialized."""
    return _engine is not None and _session_factory is not None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the active session factory; raise if lifecycle not started."""
    if _session_factory is None:
        raise RuntimeError(
            "DB session factory not initialized; call init_db_engine during lifespan first"
        )
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async session from the active factory."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
