"""Recruitment task endpoints for the course MVP API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from recruitment_assistant_agent.api.dependencies import RequestIdDep
from recruitment_assistant_agent.api.v1.schemas.recruitment_tasks import (
    RecruitmentAnalysisResponse,
    RecruitmentMaterialResponse,
    RecruitmentMaterialSummary,
    RecruitmentTaskCreateRequest,
    RecruitmentTaskCreateResponse,
    RecruitmentTaskDetailEnvelope,
    RecruitmentTaskDetailResponse,
    RecruitmentTaskListResponse,
    RecruitmentTaskResponse,
)
from recruitment_assistant_agent.application.services.recruit_task_api_service import (
    RecruitmentAnalysisRecord,
    RecruitmentTaskApiService,
    RecruitmentTaskRecord,
    get_recruitment_task_api_service,
)
from recruitment_assistant_agent.domain.value_objects.recruit_enums import (
    MaterialKind,
    ReviewStatus,
    TaskStatus,
)

router = APIRouter()

TaskServiceDep = Annotated[
    RecruitmentTaskApiService,
    Depends(get_recruitment_task_api_service),
]


@router.post(
    "/recruitment-tasks",
    response_model=RecruitmentTaskCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recruitment_task(
    payload: RecruitmentTaskCreateRequest,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentTaskCreateResponse:
    """Create a recruitment task with optional text materials."""
    task = service.create_task(
        title=payload.title,
        priority=payload.priority,
        resume_text=payload.resume_text,
        jd_text=payload.jd_text,
    )
    return RecruitmentTaskCreateResponse(
        request_id=request_id,
        task=_task_response(task),
    )


@router.get("/recruitment-tasks", response_model=RecruitmentTaskListResponse)
async def list_recruitment_tasks(
    request_id: RequestIdDep,
    service: TaskServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    review_status: ReviewStatus | None = None,
) -> RecruitmentTaskListResponse:
    """List recruitment tasks for the MVP demo scope."""
    result = service.list_tasks(
        page=page,
        page_size=page_size,
        status=task_status,
        review_status=review_status,
    )
    return RecruitmentTaskListResponse(
        request_id=request_id,
        items=[_task_response(task) for task in result.items],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


@router.get(
    "/recruitment-tasks/{task_id}",
    response_model=RecruitmentTaskDetailEnvelope,
)
async def get_recruitment_task(
    task_id: str,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentTaskDetailEnvelope:
    """Return one recruitment task and its material metadata."""
    return RecruitmentTaskDetailEnvelope(
        request_id=request_id,
        task=_task_detail_response(service.get_task(task_id)),
    )


@router.delete(
    "/recruitment-tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_recruitment_task(
    task_id: str,
    service: TaskServiceDep,
) -> Response:
    """Soft-delete one recruitment task in the MVP task store."""
    service.delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _task_response(task: RecruitmentTaskRecord) -> RecruitmentTaskResponse:
    return RecruitmentTaskResponse(
        task_id=task.task_id,
        title=task.title,
        priority=task.priority,
        status=task.status,
        review_status=task.review_status,
        material_summary=_material_summary(task),
        latest_run_id=task.latest_run_id,
        created_at=task.created_at,
    )


def _task_detail_response(task: RecruitmentTaskRecord) -> RecruitmentTaskDetailResponse:
    response = _task_response(task)
    return RecruitmentTaskDetailResponse(
        **response.model_dump(),
        materials=[
            RecruitmentMaterialResponse(
                material_id=material.material_id,
                kind=material.kind.value,
                scan_status=material.scan_status,
                original_deleted=material.original_deleted,
                size_chars=material.size_chars,
            )
            for material in task.materials
        ],
        analysis=_analysis_response(task.analysis),
    )


def _material_summary(task: RecruitmentTaskRecord) -> RecruitmentMaterialSummary:
    resume = next(
        (material for material in task.materials if material.kind == MaterialKind.RESUME),
        None,
    )
    jd = next(
        (material for material in task.materials if material.kind == MaterialKind.JD),
        None,
    )
    return RecruitmentMaterialSummary(
        has_resume=resume is not None,
        has_jd=jd is not None,
        resume_material_id=resume.material_id if resume else None,
        jd_material_id=jd.material_id if jd else None,
    )


def _analysis_response(
    analysis: RecruitmentAnalysisRecord | None,
) -> RecruitmentAnalysisResponse | None:
    if analysis is None:
        return None
    return RecruitmentAnalysisResponse(
        rule_version=analysis.rule_version,
        candidate_summary=analysis.candidate_summary,
        job_title=analysis.job_title,
        match_score=analysis.match_score,
        match_tier=analysis.match_tier,
        matched_keywords=list(analysis.matched_keywords),
        missing_keywords=list(analysis.missing_keywords),
        risk_points=list(analysis.risk_points),
        interview_questions=list(analysis.interview_questions),
        fairness_note=analysis.fairness_note,
        workflow_nodes=list(analysis.workflow_nodes),
    )
