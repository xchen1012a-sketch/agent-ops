"""Schemas for recruitment report API endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RecruitmentReportSummary(BaseModel):
    report_id: str
    task_id: str
    status: str
    format_available: list[str]
    expires_at: datetime


class RecruitmentReportDetail(RecruitmentReportSummary):
    content_markdown: str


class RecruitmentReportCreateEnvelope(BaseModel):
    request_id: str
    report: RecruitmentReportSummary


class RecruitmentReportDetailEnvelope(BaseModel):
    request_id: str
    report: RecruitmentReportDetail
