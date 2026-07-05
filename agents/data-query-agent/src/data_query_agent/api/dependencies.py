"""FastAPI dependencies: settings, request-scoped DB session, request id."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.application.services.identity_service import IdentityThreadService
from data_query_agent.application.services.run_service import QueryRunTraceService
from data_query_agent.core.config import Settings, get_settings
from data_query_agent.core.errors import AuthError
from data_query_agent.core.request_context import REQUEST_ID_KEY, request_context
from data_query_agent.infrastructure.db.repositories.identity import SqlAlchemyIdentityRepository
from data_query_agent.infrastructure.db.repositories.run import SqlAlchemyRunRepository
from data_query_agent.infrastructure.db.session import get_session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async DB session; rollback on unhandled error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_current_subject(x_user_subject: str | None = Header(default=None)) -> str:
    """Return authenticated upstream subject from gateway-provided header."""
    if x_user_subject is None or not x_user_subject.strip():
        raise AuthError("X-User-Subject header is required")
    return x_user_subject.strip()


def get_identity_thread_service(session: SessionDep) -> IdentityThreadService:
    """Build identity/thread service for request-scoped persistence."""
    return IdentityThreadService(SqlAlchemyIdentityRepository(session))


def get_query_run_trace_service(session: SessionDep) -> QueryRunTraceService:
    """Build query run trace service for request-scoped persistence."""
    return QueryRunTraceService(SqlAlchemyRunRepository(session))


def get_request_id(request: Request) -> str:
    """Return the request id assigned by middleware; fall back to header or unknown."""
    value = request_context.get(REQUEST_ID_KEY)
    if isinstance(value, str) and value:
        return value
    return request.headers.get("x-request-id", "unknown")


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
CurrentSubjectDep = Annotated[str, Depends(get_current_subject)]
IdentityThreadServiceDep = Annotated[IdentityThreadService, Depends(get_identity_thread_service)]
QueryRunTraceServiceDep = Annotated[QueryRunTraceService, Depends(get_query_run_trace_service)]
