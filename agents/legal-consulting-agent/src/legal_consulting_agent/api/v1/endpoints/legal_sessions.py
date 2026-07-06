"""Legal consultation session endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalDataServiceDep,
    LegalStreamAdapterDep,
)
from legal_consulting_agent.api.v1.schemas.legal_sessions import (
    LegalSessionCreateEnvelope,
    LegalSessionCreateRequest,
    LegalSessionEnvelope,
    LegalSessionListData,
    LegalSessionListEnvelope,
    LegalSessionRenameRequest,
    LegalSessionResponse,
)
from legal_consulting_agent.application.services.title_service import LegalTitleService
from legal_consulting_agent.domain.entities.legal_data import LegalSession
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole

_TITLE_CONTEXT_LIMIT = 4

router = APIRouter()


def _to_session_response(session: LegalSession) -> LegalSessionResponse:
    return LegalSessionResponse(
        public_id=session.public_id,
        title=session.title,
        status=session.status,
        last_message_at=session.last_message_at,
    )


@router.post(
    "/sessions",
    response_model=LegalSessionCreateEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    payload: LegalSessionCreateRequest,
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
) -> LegalSessionCreateEnvelope:
    """Create a user-owned legal consultation session."""

    session = await legal_data_service.create_session(
        user_public_id=user_public_id,
        category_code=payload.category_code,
        title=payload.title,
    )
    return LegalSessionCreateEnvelope(data=_to_session_response(session))


@router.get("/sessions", response_model=LegalSessionListEnvelope)
async def list_sessions(
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LegalSessionListEnvelope:
    """List the caller's consultation sessions so they survive a page refresh."""

    sessions = await legal_data_service.list_sessions(
        user_public_id=user_public_id,
        limit=limit,
        offset=offset,
    )
    return LegalSessionListEnvelope(
        data=LegalSessionListData(
            items=[_to_session_response(session) for session in sessions],
            limit=limit,
            offset=offset,
        )
    )


@router.patch("/sessions/{session_public_id}", response_model=LegalSessionEnvelope)
async def rename_session(
    session_public_id: str,
    payload: LegalSessionRenameRequest,
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
) -> LegalSessionEnvelope:
    """Rename a user-owned session."""

    session = await legal_data_service.rename_session(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        title=payload.title,
    )
    return LegalSessionEnvelope(data=_to_session_response(session))


@router.post("/sessions/{session_public_id}/title", response_model=LegalSessionEnvelope)
async def generate_session_title(
    session_public_id: str,
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
    stream_adapter: LegalStreamAdapterDep,
) -> LegalSessionEnvelope:
    """Auto-name a session from its first exchange (LLM, deterministic fallback)."""

    messages = await legal_data_service.list_recent_session_messages(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        limit=_TITLE_CONTEXT_LIMIT,
    )
    first_question = next(
        (message.content for message in messages if message.role is MessageRole.USER),
        "",
    )
    answer = next(
        (message.content for message in messages if message.role is MessageRole.ASSISTANT),
        None,
    )
    title = await LegalTitleService(llm_adapter=stream_adapter).generate_title(
        first_question=first_question,
        answer=answer,
    )
    session = await legal_data_service.rename_session(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        title=title,
    )
    return LegalSessionEnvelope(data=_to_session_response(session))
