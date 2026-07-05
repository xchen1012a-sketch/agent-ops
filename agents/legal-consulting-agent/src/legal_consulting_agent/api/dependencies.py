"""FastAPI dependencies: settings, request-scoped DB session, request id."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from legal_consulting_agent.application.services import LegalDataService, LegalQuestionAnswerService
from legal_consulting_agent.core.config import Settings, get_settings
from legal_consulting_agent.core.errors import AuthError
from legal_consulting_agent.core.request_context import REQUEST_ID_KEY, request_context
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


def get_legal_data_service(session: SessionDep) -> LegalDataService:
    """Build the LEGAL data application service for request handlers."""

    return LegalDataService(SqlAlchemyLegalDataRepository(session))


def get_legal_question_answer_service(
    legal_data_service: LegalDataServiceDep,
) -> LegalQuestionAnswerService:
    """Build the deterministic question-answer application service."""

    return LegalQuestionAnswerService(legal_data_service=legal_data_service)


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
CurrentUserPublicIdDep = Annotated[str, Depends(get_current_user_public_id)]
LegalDataServiceDep = Annotated[LegalDataService, Depends(get_legal_data_service)]
LegalQuestionAnswerServiceDep = Annotated[
    LegalQuestionAnswerService,
    Depends(get_legal_question_answer_service),
]
