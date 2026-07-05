"""Pytest fixtures shared across the legal-consulting-agent test suite."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from legal_consulting_agent.infrastructure.db import session as db_session
from legal_consulting_agent.main import create_app


@pytest.fixture
def reset_db_state() -> None:
    """Ensure each test starts without an engine bound to stale state."""
    db_session._engine = None
    db_session._session_factory = None


@pytest_asyncio.fixture
async def app_client(reset_db_state: None) -> AsyncIterator[AsyncClient]:
    """Yield an HTTP client bound to the FastAPI app without running lifespan.

    Lifespan is intentionally skipped so tests do not require live MySQL.
    Use the ``health/live`` endpoint or unit-level tests for smoke checks.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
