"""DTOs for legal high-risk review APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from legal_consulting_agent.domain.value_objects.legal_enums import ReviewStatus


class LegalHighRiskReviewCreateRequest(BaseModel):
    """Request body for queueing a high-risk assistant message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=1, max_length=200)


class LegalHighRiskReviewResponse(BaseModel):
    """Public high-risk review projection returned by the API."""

    id: int | None
    reason: str
    status: ReviewStatus


class LegalHighRiskReviewCreateEnvelope(BaseModel):
    """Success envelope for high-risk review queueing."""

    data: LegalHighRiskReviewResponse
    error: Literal[None] = None


class LegalHighRiskReviewAdminResponse(BaseModel):
    """Administrator projection for high-risk review queues."""

    id: int | None
    message_id: int
    user_id: int
    reason: str
    status: ReviewStatus
    reviewed_by: int | None
    resolution: str | None


class LegalHighRiskReviewListData(BaseModel):
    """Paginated administrator high-risk review list."""

    items: list[LegalHighRiskReviewAdminResponse]
    limit: int
    offset: int
    status: ReviewStatus


class LegalHighRiskReviewListEnvelope(BaseModel):
    """Success envelope for administrator high-risk review list."""

    data: LegalHighRiskReviewListData
    error: Literal[None] = None


class LegalHighRiskReviewResolveRequest(BaseModel):
    """Request body for administrator high-risk review resolution."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: ReviewStatus
    resolution: str = Field(min_length=1, max_length=1000)

    @field_validator("status")
    @classmethod
    def reject_pending_status(cls, value: ReviewStatus) -> ReviewStatus:
        """Resolution endpoint may only move reviews out of pending."""

        if value is ReviewStatus.PENDING:
            raise ValueError("status must be reviewed or resolved")
        return value


class LegalHighRiskReviewResolveEnvelope(BaseModel):
    """Success envelope for administrator high-risk review resolution."""

    data: LegalHighRiskReviewAdminResponse
    error: Literal[None] = None
