"""Legal session message endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalDataServiceDep,
)
from legal_consulting_agent.api.v1.schemas.legal_messages import (
    LegalMessageListData,
    LegalMessageListEnvelope,
    LegalMessageResponse,
)
from legal_consulting_agent.domain.entities.legal_data import LegalMessage

router = APIRouter()


def _to_message_response(message: LegalMessage) -> LegalMessageResponse:
    return LegalMessageResponse(
        public_id=message.public_id,
        role=message.role,
        content=message.content,
        citations=message.citations,
        high_risk=message.high_risk,
        prompt_version=message.prompt_version,
    )


@router.get(
    "/sessions/{session_public_id}/messages",
    response_model=LegalMessageListEnvelope,
)
async def list_session_messages(
    session_public_id: str,
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LegalMessageListEnvelope:
    """List messages for a user-owned legal consultation session."""

    messages = await legal_data_service.list_session_messages(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        limit=limit,
        offset=offset,
    )
    return LegalMessageListEnvelope(
        data=LegalMessageListData(
            items=[_to_message_response(message) for message in messages],
            limit=limit,
            offset=offset,
        )
    )
