"""Legal feedback endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalDataServiceDep,
)
from legal_consulting_agent.api.v1.schemas.legal_feedbacks import (
    LegalFeedbackCreateEnvelope,
    LegalFeedbackCreateRequest,
    LegalFeedbackResponse,
)
from legal_consulting_agent.domain.entities.legal_data import Feedback

router = APIRouter()


def _to_feedback_response(feedback: Feedback) -> LegalFeedbackResponse:
    return LegalFeedbackResponse(
        id=feedback.id,
        rating=feedback.rating,
        comment=feedback.comment,
    )


@router.post(
    "/sessions/{session_public_id}/messages/{message_public_id}/feedback",
    response_model=LegalFeedbackCreateEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_feedback(
    session_public_id: str,
    message_public_id: str,
    payload: LegalFeedbackCreateRequest,
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
) -> LegalFeedbackCreateEnvelope:
    """Create feedback for an assistant answer in a user-owned session."""

    feedback = await legal_data_service.create_feedback(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        message_public_id=message_public_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    return LegalFeedbackCreateEnvelope(data=_to_feedback_response(feedback))
