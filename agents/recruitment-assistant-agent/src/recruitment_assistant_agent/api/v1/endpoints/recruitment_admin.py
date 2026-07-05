"""Recruitment admin review endpoints for the course MVP."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from recruitment_assistant_agent.api.dependencies import RequestIdDep
from recruitment_assistant_agent.api.v1.endpoints.recruitment_runs import _run_response
from recruitment_assistant_agent.api.v1.endpoints.recruitment_tasks import _task_detail_response
from recruitment_assistant_agent.api.v1.schemas.recruitment_admin import (
    RecruitmentAdminTaskEnvelope,
    RecruitmentManualOverrideEnvelope,
    RecruitmentManualOverrideRequest,
    RecruitmentManualOverrideResponse,
    RecruitmentReviewEnvelope,
    RecruitmentReviewRequest,
    RecruitmentReviewResponse,
)
from recruitment_assistant_agent.application.services.recruit_task_api_service import (
    RecruitmentManualOverrideRecord,
    RecruitmentReviewRecord,
    RecruitmentTaskApiService,
    get_recruitment_task_api_service,
)

router = APIRouter()

TaskServiceDep = Annotated[
    RecruitmentTaskApiService,
    Depends(get_recruitment_task_api_service),
]


@router.get("/admin/recruitment-tasks/{task_id}", response_model=RecruitmentAdminTaskEnvelope)
async def get_admin_recruitment_task(
    task_id: str,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentAdminTaskEnvelope:
    """Return task details plus latest run and review metadata for admin UI."""
    task = service.get_task(task_id)
    latest_run = service.get_run(task.latest_run_id) if task.latest_run_id else None
    review = service.get_task_review(task_id)
    return RecruitmentAdminTaskEnvelope(
        request_id=request_id,
        task=_task_detail_response(task),
        latest_run=_run_response(latest_run) if latest_run else None,
        review=_review_response(review) if review else None,
    )


@router.post("/admin/recruitment-tasks/{task_id}/review", response_model=RecruitmentReviewEnvelope)
async def review_recruitment_task(
    task_id: str,
    payload: RecruitmentReviewRequest,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentReviewEnvelope:
    """Record an MVP admin review decision for one task."""
    review = service.review_task(
        task_id=task_id,
        review_status=payload.review_status,
        review_note=payload.review_note,
        reviewed_by="admin_mvp",
    )
    return RecruitmentReviewEnvelope(
        request_id=request_id,
        review=_review_response(review),
    )


@router.post(
    "/admin/match-results/{match_result_id}/override",
    response_model=RecruitmentManualOverrideEnvelope,
)
async def create_match_result_override(
    match_result_id: str,
    payload: RecruitmentManualOverrideRequest,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentManualOverrideEnvelope:
    """Record a mock manual override for one match result field."""
    override = service.create_manual_override(
        match_result_id=match_result_id,
        field_path=payload.field_path,
        new_value=payload.new_value,
        reason=payload.reason,
    )
    return RecruitmentManualOverrideEnvelope(
        request_id=request_id,
        override=_override_response(override),
    )


def _review_response(review: RecruitmentReviewRecord) -> RecruitmentReviewResponse:
    return RecruitmentReviewResponse(
        task_id=review.task_id,
        review_status=review.review_status,
        review_note=review.review_note,
        reviewed_by=review.reviewed_by,
        reviewed_at=review.reviewed_at,
    )


def _override_response(
    override: RecruitmentManualOverrideRecord,
) -> RecruitmentManualOverrideResponse:
    return RecruitmentManualOverrideResponse(
        override_id=override.override_id,
        match_result_id=override.match_result_id,
        field_path=override.field_path,
        old_value=override.old_value,
        new_value=override.new_value,
        reason=override.reason,
        created_at=override.created_at,
    )
