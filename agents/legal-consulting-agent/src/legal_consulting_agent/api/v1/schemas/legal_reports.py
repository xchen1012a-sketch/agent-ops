"""DTOs for legal consultation report APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class LegalReportResponse(BaseModel):
    """Synchronous legal report projection."""

    record_public_id: str
    format: Literal["markdown"]
    content: str


class LegalReportEnvelope(BaseModel):
    """Success envelope for report export."""

    data: LegalReportResponse
    error: Literal[None] = None
