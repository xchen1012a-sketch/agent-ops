"""DTOs for legal question answering APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from legal_consulting_agent.workflows.legal_state import Citation


class LegalQuestionRequest(BaseModel):
    """Request body for submitting a legal question."""

    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=4000)


class LegalMessageRef(BaseModel):
    """Public reference to a persisted legal message."""

    public_id: str


class LegalQuestionAnswerResponse(BaseModel):
    """Response projection for a deterministic legal answer."""

    question_message: LegalMessageRef
    answer_message: LegalMessageRef
    answer: str
    citations: list[Citation]
    high_risk: bool
    risk_reason: str | None
    category: str | None
    node_trace: list[str]


class LegalQuestionAnswerEnvelope(BaseModel):
    """Success envelope for question answering."""

    data: LegalQuestionAnswerResponse
    error: Literal[None] = None
