"""Unit tests for async DB session lifecycle using mocks (no real DB)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from data_query_agent.core.config import Settings
from data_query_agent.infrastructure.db import session as db_session


def _make_settings() -> Settings:
    return Settings(
        jwt_secret="x" * 32,
        database_url="mysql+asyncmy://u:p@mysql:3306/db",
        deepseek_api_key="sk-test",
    )


@pytest.mark.asyncio
async def test_init_db_engine_creates_engine_and_factory() -> None:
    db_session._engine = None
    db_session._session_factory = None

    mock_engine = MagicMock()
    mock_factory = MagicMock()
    with (
        patch.object(db_session, "create_async_engine", return_value=mock_engine) as mock_create,
        patch.object(db_session, "async_sessionmaker", return_value=mock_factory) as mock_maker,
    ):
        await db_session.init_db_engine(_make_settings())

    mock_create.assert_called_once()
    assert mock_create.call_args.kwargs["pool_size"] == 10
    assert mock_create.call_args.kwargs["max_overflow"] == 20
    assert mock_create.call_args.kwargs["pool_pre_ping"] is True
    mock_maker.assert_called_once()
    assert db_session.is_engine_ready() is True
    assert db_session.get_session_factory() is mock_factory

    db_session._engine = None
    db_session._session_factory = None


@pytest.mark.asyncio
async def test_close_db_engine_disposes_engine_and_resets_state() -> None:
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()
    mock_factory = MagicMock()
    db_session._engine = mock_engine
    db_session._session_factory = mock_factory

    await db_session.close_db_engine()

    mock_engine.dispose.assert_awaited_once()
    assert db_session._engine is None
    assert db_session._session_factory is None
    assert db_session.is_engine_ready() is False


@pytest.mark.asyncio
async def test_close_db_engine_is_noop_when_not_initialized() -> None:
    db_session._engine = None
    db_session._session_factory = None
    await db_session.close_db_engine()
    assert db_session.is_engine_ready() is False


def test_get_session_factory_raises_before_init() -> None:
    db_session._engine = None
    db_session._session_factory = None
    with pytest.raises(RuntimeError, match="DB session factory not initialized"):
        db_session.get_session_factory()
