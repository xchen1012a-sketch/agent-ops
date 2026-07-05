"""DTOs for legal high-risk review APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
