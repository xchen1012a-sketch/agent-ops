"""DTOs for legal consultation session APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from legal_consulting_agent.domain.value_objects.legal_enums import SessionStatus


class LegalSessionCreateRequest(BaseModel):
    """Request body for creating a legal consultation session."""

    model_config = ConfigDict(str_strip_whitespace=True)

    category_code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    title: str | None = Field(default=None, max_length=120)


class LegalSessionResponse(BaseModel):
    """Public session projection returned by the API."""

    public_id: str
    title: str | None
    status: SessionStatus
    last_message_at: datetime | None


class LegalSessionCreateEnvelope(BaseModel):
    """Success envelope for session creation."""

    data: LegalSessionResponse
    error: Literal[None] = None


class LegalSessionEnvelope(BaseModel):
    """Success envelope for a single session (e.g. rename)."""

    data: LegalSessionResponse
    error: Literal[None] = None


class LegalSessionListData(BaseModel):
    """Paginated list of the caller's sessions, newest first."""

    items: list[LegalSessionResponse]
    limit: int
    offset: int


class LegalSessionListEnvelope(BaseModel):
    """Success envelope for the session list."""

    data: LegalSessionListData
    error: Literal[None] = None


class LegalSessionRenameRequest(BaseModel):
    """Request body for renaming a session."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
