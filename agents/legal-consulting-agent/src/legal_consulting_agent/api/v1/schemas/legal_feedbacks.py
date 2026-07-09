"""DTOs for legal feedback APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LegalFeedbackCreateRequest(BaseModel):
    """Request body for creating feedback for an assistant message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class LegalFeedbackResponse(BaseModel):
    """Public feedback projection returned by the API."""

    id: int | None
    rating: int
    comment: str | None


class LegalFeedbackCreateEnvelope(BaseModel):
    """Success envelope for feedback creation."""

    data: LegalFeedbackResponse
    error: Literal[None] = None
