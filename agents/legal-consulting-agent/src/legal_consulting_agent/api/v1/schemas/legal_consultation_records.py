"""DTOs for legal consultation record history APIs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class LegalConsultationRecordResponse(BaseModel):
    """Public projection for one consultation record in history lists."""

    public_id: str
    summary: str
    citations: list[dict[str, Any]] | None
    high_risk: bool
    disclaimer: str


class LegalConsultationRecordListData(BaseModel):
    """Paginated consultation record list response data."""

    items: list[LegalConsultationRecordResponse]
    limit: int
    offset: int
    query: str | None


class LegalConsultationRecordListEnvelope(BaseModel):
    """Success envelope for consultation record history queries."""

    data: LegalConsultationRecordListData
    error: Literal[None] = None
