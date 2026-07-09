"""Legal high-risk review endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalDataServiceDep,
)
from legal_consulting_agent.api.v1.schemas.legal_reviews import (
    LegalHighRiskReviewCreateEnvelope,
    LegalHighRiskReviewCreateRequest,
    LegalHighRiskReviewResponse,
)
from legal_consulting_agent.domain.entities.legal_data import HighRiskReview

router = APIRouter()


def _to_review_response(review: HighRiskReview) -> LegalHighRiskReviewResponse:
    return LegalHighRiskReviewResponse(
        id=review.id,
        reason=review.reason,
        status=review.status,
    )


@router.post(
    "/sessions/{session_public_id}/messages/{message_public_id}/high-risk-review",
    response_model=LegalHighRiskReviewCreateEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_high_risk_review(
    session_public_id: str,
    message_public_id: str,
    payload: LegalHighRiskReviewCreateRequest,
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
) -> LegalHighRiskReviewCreateEnvelope:
    """Queue a high-risk assistant message for later review."""

    review = await legal_data_service.create_high_risk_review(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        message_public_id=message_public_id,
        reason=payload.reason,
    )
    return LegalHighRiskReviewCreateEnvelope(data=_to_review_response(review))
