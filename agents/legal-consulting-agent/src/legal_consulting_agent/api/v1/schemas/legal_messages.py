"""DTOs for legal session message APIs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole


class LegalMessageResponse(BaseModel):
    """Public message projection returned by the API."""

    public_id: str
    role: MessageRole
    content: str
    citations: list[dict[str, Any]] | None
    high_risk: bool
    prompt_version: str | None


class LegalMessageListData(BaseModel):
    """Paginated message list payload."""

    items: list[LegalMessageResponse]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class LegalMessageListEnvelope(BaseModel):
    """Success envelope for session message listing."""

    data: LegalMessageListData
    error: Literal[None] = None
