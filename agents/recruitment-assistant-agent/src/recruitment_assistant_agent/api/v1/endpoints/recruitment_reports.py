"""Recruitment report endpoints for the course MVP."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from recruitment_assistant_agent.api.dependencies import RequestIdDep
from recruitment_assistant_agent.api.v1.schemas.recruitment_reports import (
    RecruitmentReportCreateEnvelope,
    RecruitmentReportDetail,
    RecruitmentReportDetailEnvelope,
    RecruitmentReportSummary,
)
from recruitment_assistant_agent.application.services.recruit_task_api_service import (
    RecruitmentReportRecord,
    RecruitmentTaskApiService,
    get_recruitment_task_api_service,
)

router = APIRouter()

TaskServiceDep = Annotated[
    RecruitmentTaskApiService,
    Depends(get_recruitment_task_api_service),
]
ReportFormatQuery = Annotated[str, Query(alias="format", pattern="^(md|pdf)$")]


@router.post(
    "/recruitment-tasks/{task_id}/reports",
    response_model=RecruitmentReportCreateEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_recruitment_report(
    task_id: str,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentReportCreateEnvelope:
    """Generate a mock recruitment report after admin approval."""
    report = service.create_report(task_id)
    return RecruitmentReportCreateEnvelope(
        request_id=request_id,
        report=_report_summary(report),
    )


@router.get("/recruitment-reports/{report_id}", response_model=RecruitmentReportDetailEnvelope)
async def get_recruitment_report(
    report_id: str,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentReportDetailEnvelope:
    """Return one generated recruitment report."""
    report = service.get_report(report_id)
    return RecruitmentReportDetailEnvelope(
        request_id=request_id,
        report=RecruitmentReportDetail(
            **_report_summary(report).model_dump(),
            content_markdown=report.content_markdown,
        ),
    )


@router.get("/recruitment-reports/{report_id}/export")
async def export_recruitment_report(
    report_id: str,
    service: TaskServiceDep,
    report_format: ReportFormatQuery = "md",
) -> Response:
    """Export one report as Markdown or mock PDF bytes."""
    media_type, content, filename = service.export_report(report_id, report_format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )


def _report_summary(report: RecruitmentReportRecord) -> RecruitmentReportSummary:
    return RecruitmentReportSummary(
        report_id=report.report_id,
        task_id=report.task_id,
        status=report.status,
        format_available=list(report.format_available),
        expires_at=report.expires_at,
    )
