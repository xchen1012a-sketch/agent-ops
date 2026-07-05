"""Schemas for recruitment admin review endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from recruitment_assistant_agent.api.v1.schemas.recruitment_runs import RecruitmentRunResponse
from recruitment_assistant_agent.api.v1.schemas.recruitment_tasks import (
    RecruitmentTaskDetailResponse,
)
from recruitment_assistant_agent.domain.value_objects.recruit_enums import ReviewStatus


class RecruitmentAdminTaskEnvelope(BaseModel):
    request_id: str
    task: RecruitmentTaskDetailResponse
    latest_run: RecruitmentRunResponse | None
    review: RecruitmentReviewResponse | None


class RecruitmentReviewRequest(BaseModel):
    review_status: ReviewStatus
    review_note: str | None = Field(default=None, max_length=1_000)


class RecruitmentReviewResponse(BaseModel):
    task_id: str
    review_status: ReviewStatus
    review_note: str | None
    reviewed_by: str
    reviewed_at: datetime


class RecruitmentReviewEnvelope(BaseModel):
    request_id: str
    review: RecruitmentReviewResponse


class RecruitmentManualOverrideRequest(BaseModel):
    field_path: str = Field(min_length=1, max_length=120)
    new_value: str = Field(min_length=1, max_length=1_000)
    reason: str = Field(min_length=1, max_length=1_000)


class RecruitmentManualOverrideResponse(BaseModel):
    override_id: str
    match_result_id: str
    field_path: str
    old_value: str | None
    new_value: str
    reason: str
    created_at: datetime


class RecruitmentManualOverrideEnvelope(BaseModel):
    request_id: str
    override: RecruitmentManualOverrideResponse
