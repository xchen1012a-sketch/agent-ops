"""Application service for legal consultation report projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from legal_consulting_agent.application.services.legal_data_service import LegalDataService
from legal_consulting_agent.domain.entities.legal_data import ConsultationRecord


@dataclass(frozen=True, slots=True)
class LegalConsultationReport:
    """Synchronous report projection for a completed consultation record."""

    record_public_id: str
    format: str
    content: str


class LegalReportService:
    """Build user-owned legal consultation report projections."""

    def __init__(self, legal_data_service: LegalDataService) -> None:
        self._legal_data_service = legal_data_service

    async def build_markdown_report(
        self,
        *,
        user_public_id: str,
        record_public_id: str,
    ) -> LegalConsultationReport:
        """Return a Markdown report for a user-owned consultation record."""

        record = await self._legal_data_service.get_consultation_record(
            user_public_id=user_public_id,
            record_public_id=record_public_id,
        )
        return LegalConsultationReport(
            record_public_id=record.public_id,
            format="markdown",
            content=_render_markdown(record),
        )


def _render_markdown(record: ConsultationRecord) -> str:
    citations = _render_citations(record.citations)
    risk = "yes" if record.high_risk else "no"
    return "\n".join(
        [
            "# Legal Consultation Report",
            "",
            f"- Record: {record.public_id}",
            f"- High risk: {risk}",
            "",
            "## Summary",
            record.summary,
            "",
            "## Citations",
            citations,
            "",
            "## Disclaimer",
            record.disclaimer,
            "",
        ]
    )


def _render_citations(citations: list[dict[str, Any]] | None) -> str:
    if not citations:
        return "No citations."
    lines: list[str] = []
    for index, citation in enumerate(citations, start=1):
        source = citation.get("source") or citation.get("source_name") or "Unknown source"
        section = citation.get("section") or citation.get("source_section") or "Unknown section"
        snippet = citation.get("snippet") or ""
        lines.append(f"{index}. {source} {section}: {snippet}")
    return "\n".join(lines)
