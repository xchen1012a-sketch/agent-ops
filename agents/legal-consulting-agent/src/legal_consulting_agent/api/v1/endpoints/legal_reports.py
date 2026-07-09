"""Legal consultation report endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from legal_consulting_agent.api.dependencies import CurrentUserPublicIdDep, LegalReportServiceDep
from legal_consulting_agent.api.v1.schemas.legal_reports import (
    LegalReportEnvelope,
    LegalReportResponse,
)
from legal_consulting_agent.application.services import LegalConsultationReport

router = APIRouter()


def _to_report_response(report: LegalConsultationReport) -> LegalReportResponse:
    return LegalReportResponse(
        record_public_id=report.record_public_id,
        format="markdown",
        content=report.content,
    )


@router.get(
    "/consultation-records/{record_public_id}/report",
    response_model=LegalReportEnvelope,
)
async def export_consultation_report(
    record_public_id: str,
    user_public_id: CurrentUserPublicIdDep,
    report_service: LegalReportServiceDep,
) -> LegalReportEnvelope:
    """Export a user-owned consultation record as a Markdown report projection."""

    report = await report_service.build_markdown_report(
        user_public_id=user_public_id,
        record_public_id=record_public_id,
    )
    return LegalReportEnvelope(data=_to_report_response(report))
