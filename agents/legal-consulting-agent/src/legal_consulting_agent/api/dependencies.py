"""FastAPI dependencies: settings, request-scoped DB session, request id."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from legal_consulting_agent.application.services import (
    LegalDataService,
    LegalQuestionAnswerService,
    LegalReportService,
    LegalRunControlService,
)
from legal_consulting_agent.application.services.agent_api_config import ApiConfigCrypto
from legal_consulting_agent.core.config import Settings, get_settings
from legal_consulting_agent.core.errors import AuthError, ForbiddenError
from legal_consulting_agent.core.request_context import REQUEST_ID_KEY, request_context
from legal_consulting_agent.infrastructure.db.repositories.agent_api_config import (
    SqlAlchemyAgentApiConfigRepository,
)
from legal_consulting_agent.infrastructure.db.repositories.legal_data import (
    SqlAlchemyLegalDataRepository,
)
from legal_consulting_agent.infrastructure.db.session import get_session_factory


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


def get_request_id(request: Request) -> str:
    """Return the request id assigned by middleware; fall back to header or unknown."""
    value = request_context.get(REQUEST_ID_KEY)
    if isinstance(value, str) and value:
        return value
    return request.headers.get("x-request-id", "unknown")


def get_current_user_public_id(
    x_user_public_id: Annotated[str | None, Header(alias="x-user-public-id")] = None,
) -> str:
    """Return the trusted upstream user public id from the request boundary."""

    if x_user_public_id is None or not x_user_public_id.strip():
        raise AuthError("User identity header is required")
    return x_user_public_id.strip()


def get_current_user_role(
    x_user_role: Annotated[str | None, Header(alias="x-user-role")] = None,
) -> str:
    """Return the trusted upstream role injected by the gateway."""

    if x_user_role is None or not x_user_role.strip():
        raise AuthError("User role header is required")
    return x_user_role.strip()


def require_admin_role(
    role: Annotated[str, Depends(get_current_user_role)],
) -> str:
    """Reject non-admin callers; gateway-injected role is the trust boundary."""

    if role.lower() != "admin":
        raise ForbiddenError("Admin role required")
    return role


def get_agent_api_config_crypto(settings: SettingsDep) -> ApiConfigCrypto:
    """Build the Fernet crypto service from settings."""

    return ApiConfigCrypto(settings.agent_config_encryption_key.get_secret_value())


def get_agent_api_config_repository(session: SessionDep) -> SqlAlchemyAgentApiConfigRepository:
    """Build the agent_api_config repository for the request scope."""

    return SqlAlchemyAgentApiConfigRepository(session)


def get_legal_data_service(session: SessionDep) -> LegalDataService:
    """Build the LEGAL data application service for request handlers."""

    return LegalDataService(SqlAlchemyLegalDataRepository(session))


def get_legal_question_answer_service(
    legal_data_service: LegalDataServiceDep,
) -> LegalQuestionAnswerService:
    """Build the deterministic question-answer application service."""

    return LegalQuestionAnswerService(legal_data_service=legal_data_service)


def get_legal_report_service(legal_data_service: LegalDataServiceDep) -> LegalReportService:
    """Build the legal report projection service."""

    return LegalReportService(legal_data_service)


def get_legal_run_control_service() -> LegalRunControlService:
    """Build the pure workflow run control projection service."""

    return LegalRunControlService()


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
CurrentUserPublicIdDep = Annotated[str, Depends(get_current_user_public_id)]
AdminUserDep = Annotated[str, Depends(require_admin_role)]
AgentApiConfigRepoDep = Annotated[
    SqlAlchemyAgentApiConfigRepository, Depends(get_agent_api_config_repository)
]
AgentApiConfigCryptoDep = Annotated[ApiConfigCrypto, Depends(get_agent_api_config_crypto)]
LegalDataServiceDep = Annotated[LegalDataService, Depends(get_legal_data_service)]
LegalQuestionAnswerServiceDep = Annotated[
    LegalQuestionAnswerService,
    Depends(get_legal_question_answer_service),
]
LegalReportServiceDep = Annotated[LegalReportService, Depends(get_legal_report_service)]
LegalRunControlServiceDep = Annotated[
    LegalRunControlService,
    Depends(get_legal_run_control_service),
]
