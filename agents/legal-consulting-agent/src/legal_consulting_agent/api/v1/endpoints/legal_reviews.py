"""Legal high-risk review endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalDataServiceDep,
)
from legal_consulting_agent.api.v1.schemas.legal_reviews import (
    LegalHighRiskReviewAdminResponse,
    LegalHighRiskReviewCreateEnvelope,
    LegalHighRiskReviewCreateRequest,
    LegalHighRiskReviewListData,
    LegalHighRiskReviewListEnvelope,
    LegalHighRiskReviewResolveEnvelope,
    LegalHighRiskReviewResolveRequest,
    LegalHighRiskReviewResponse,
)
from legal_consulting_agent.domain.entities.legal_data import HighRiskReview
from legal_consulting_agent.domain.value_objects.legal_enums import ReviewStatus

router = APIRouter()


def _to_review_response(review: HighRiskReview) -> LegalHighRiskReviewResponse:
    return LegalHighRiskReviewResponse(
        id=review.id,
        reason=review.reason,
        status=review.status,
    )


def _to_admin_review_response(review: HighRiskReview) -> LegalHighRiskReviewAdminResponse:
    return LegalHighRiskReviewAdminResponse(
        id=review.id,
        message_id=review.message_id,
        user_id=review.user_id,
        reason=review.reason,
        status=review.status,
        reviewed_by=review.reviewed_by,
        resolution=review.resolution,
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


@router.get(
    "/high-risk-reviews",
    response_model=LegalHighRiskReviewListEnvelope,
)
async def list_high_risk_reviews(
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
    review_status: Annotated[ReviewStatus, Query(alias="status")] = ReviewStatus.PENDING,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LegalHighRiskReviewListEnvelope:
    """List high-risk reviews for administrator queues."""

    reviews = await legal_data_service.list_high_risk_reviews(
        reviewer_public_id=user_public_id,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )
    return LegalHighRiskReviewListEnvelope(
        data=LegalHighRiskReviewListData(
            items=[_to_admin_review_response(review) for review in reviews],
            limit=limit,
            offset=offset,
            status=review_status,
        )
    )


@router.post(
    "/high-risk-reviews/{review_id}/resolution",
    response_model=LegalHighRiskReviewResolveEnvelope,
)
async def resolve_high_risk_review(
    review_id: int,
    payload: LegalHighRiskReviewResolveRequest,
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
) -> LegalHighRiskReviewResolveEnvelope:
    """Resolve or mark reviewed a high-risk review as an administrator."""

    review = await legal_data_service.resolve_high_risk_review(
        reviewer_public_id=user_public_id,
        review_id=review_id,
        review_status=payload.status,
        resolution=payload.resolution,
    )
    return LegalHighRiskReviewResolveEnvelope(data=_to_admin_review_response(review))
