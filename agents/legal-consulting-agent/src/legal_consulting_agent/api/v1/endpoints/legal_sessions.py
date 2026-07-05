"""Legal consultation session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalDataServiceDep,
)
from legal_consulting_agent.api.v1.schemas.legal_sessions import (
    LegalSessionCreateEnvelope,
    LegalSessionCreateRequest,
    LegalSessionResponse,
)
from legal_consulting_agent.domain.entities.legal_data import LegalSession

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
