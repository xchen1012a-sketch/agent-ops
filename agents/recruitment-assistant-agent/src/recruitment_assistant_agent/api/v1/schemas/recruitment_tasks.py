"""Schemas for recruitment task API endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from recruitment_assistant_agent.domain.value_objects.recruit_enums import (
    ReviewStatus,
    ScanStatus,
    TaskPriority,
    TaskStatus,
)


class RecruitmentTaskCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    priority: TaskPriority = TaskPriority.NORMAL
    resume_text: str | None = Field(default=None, max_length=50_000)
    jd_text: str | None = Field(default=None, max_length=50_000)


class RecruitmentMaterialSummary(BaseModel):
    has_resume: bool
    has_jd: bool
    resume_material_id: str | None = None
    jd_material_id: str | None = None


class RecruitmentMaterialResponse(BaseModel):
    material_id: str
    kind: str
    scan_status: ScanStatus
    original_deleted: bool
    size_chars: int


class RecruitmentAnalysisResponse(BaseModel):
    rule_version: str
    candidate_summary: str
    job_title: str | None
    match_score: int
    match_tier: str
    matched_keywords: list[str]
    missing_keywords: list[str]
    risk_points: list[str]
    interview_questions: list[str]
    fairness_note: str
    workflow_nodes: list[str]


class RecruitmentTaskResponse(BaseModel):
    task_id: str
    title: str | None
    priority: TaskPriority
    status: TaskStatus
    review_status: ReviewStatus
    material_summary: RecruitmentMaterialSummary
    latest_run_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecruitmentTaskDetailResponse(RecruitmentTaskResponse):
    materials: list[RecruitmentMaterialResponse]
    analysis: RecruitmentAnalysisResponse | None = None


class RecruitmentTaskCreateResponse(BaseModel):
    request_id: str
    task: RecruitmentTaskResponse


class RecruitmentTaskListResponse(BaseModel):
    request_id: str
    items: list[RecruitmentTaskResponse]
    page: int
    page_size: int
    total: int


class RecruitmentTaskDetailEnvelope(BaseModel):
    request_id: str
    task: RecruitmentTaskDetailResponse
