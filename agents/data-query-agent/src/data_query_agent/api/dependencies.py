"""FastAPI dependencies: settings, request-scoped DB session, request id."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.application.services.agent_api_config import ApiConfigCrypto
from data_query_agent.application.services.audit_service import SqlAuditService
from data_query_agent.application.services.identity_service import IdentityThreadService
from data_query_agent.application.services.run_service import QueryRunTraceService
from data_query_agent.core.config import Settings, get_settings
from data_query_agent.core.errors import AuthError
from data_query_agent.core.request_context import REQUEST_ID_KEY, request_context
from data_query_agent.infrastructure.db.repositories.agent_api_config import (
    SqlAlchemyAgentApiConfigRepository,
)
from data_query_agent.infrastructure.db.repositories.audit import SqlAlchemySqlAuditRepository
from data_query_agent.infrastructure.db.repositories.identity import SqlAlchemyIdentityRepository
from data_query_agent.infrastructure.db.repositories.run import SqlAlchemyRunRepository
from data_query_agent.infrastructure.db.session import get_session_factory
from data_query_agent.infrastructure.integrations.feishu_events import FeishuMockEventService


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


def get_agent_api_config_crypto(settings: SettingsDep) -> ApiConfigCrypto:
    """Build the Fernet crypto service from settings."""

    return ApiConfigCrypto(settings.agent_config_encryption_key.get_secret_value())


def get_agent_api_config_repository(session: SessionDep) -> SqlAlchemyAgentApiConfigRepository:
    """Build the agent_api_config repository for the request scope."""

    return SqlAlchemyAgentApiConfigRepository(session)


def get_identity_thread_service(session: SessionDep) -> IdentityThreadService:
    """Build identity/thread service for request-scoped persistence."""
    return IdentityThreadService(SqlAlchemyIdentityRepository(session))


def get_query_run_trace_service(session: SessionDep) -> QueryRunTraceService:
    """Build query run trace service for request-scoped persistence."""
    return QueryRunTraceService(SqlAlchemyRunRepository(session))


def get_sql_audit_service(session: SessionDep) -> SqlAuditService:
    """Build SQL audit service for request-scoped persistence."""
    return SqlAuditService(SqlAlchemySqlAuditRepository(session))


_feishu_mock_event_service = FeishuMockEventService()


def get_feishu_mock_event_service() -> FeishuMockEventService:
    """Return process-local mock Feishu event service for fixture tests."""
    return _feishu_mock_event_service


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
AgentApiConfigRepoDep = Annotated[
    SqlAlchemyAgentApiConfigRepository, Depends(get_agent_api_config_repository)
]
AgentApiConfigCryptoDep = Annotated[ApiConfigCrypto, Depends(get_agent_api_config_crypto)]
IdentityThreadServiceDep = Annotated[IdentityThreadService, Depends(get_identity_thread_service)]
QueryRunTraceServiceDep = Annotated[QueryRunTraceService, Depends(get_query_run_trace_service)]
SqlAuditServiceDep = Annotated[SqlAuditService, Depends(get_sql_audit_service)]
FeishuMockEventServiceDep = Annotated[
    FeishuMockEventService, Depends(get_feishu_mock_event_service)
]
