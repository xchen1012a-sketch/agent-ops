"""Recruitment run endpoints and MVP SSE stream."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from recruitment_assistant_agent.api.dependencies import RequestIdDep
from recruitment_assistant_agent.api.v1.schemas.recruitment_runs import (
    RecruitmentRunEnvelope,
    RecruitmentRunEventPayload,
    RecruitmentRunResponse,
    RecruitmentRunStartRequest,
    RecruitmentRunStartResponse,
)
from recruitment_assistant_agent.application.services.recruit_task_api_service import (
    RecruitmentRunEventRecord,
    RecruitmentRunRecord,
    RecruitmentTaskApiService,
    get_recruitment_task_api_service,
)

router = APIRouter()

TaskServiceDep = Annotated[
    RecruitmentTaskApiService,
    Depends(get_recruitment_task_api_service),
]


@router.post(
    "/recruitment-tasks/{task_id}/runs",
    response_model=RecruitmentRunStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_recruitment_run(
    task_id: str,
    payload: RecruitmentRunStartRequest,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentRunStartResponse:
    """Start a mock-backed recruitment analysis run for the MVP API."""
    run = service.start_run(
        task_id=task_id,
        prompt_version=payload.prompt_version,
        workflow_version=payload.workflow_version,
    )
    return RecruitmentRunStartResponse(
        request_id=request_id,
        run=_run_response(run),
        stream_url=f"/v1/recruitment-runs/{run.run_id}/stream",
    )


@router.get("/recruitment-runs/{run_id}", response_model=RecruitmentRunEnvelope)
async def get_recruitment_run(
    run_id: str,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentRunEnvelope:
    """Return one recruitment run status."""
    return RecruitmentRunEnvelope(
        request_id=request_id,
        run=_run_response(service.get_run(run_id)),
    )


@router.get("/recruitment-runs/{run_id}/stream")
async def stream_recruitment_run(
    run_id: str,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> StreamingResponse:
    """Stream MVP run events as SSE lines."""
    events = service.list_run_events(run_id)
    return StreamingResponse(
        _sse_lines(events, request_id=request_id),
        media_type="text/event-stream",
    )


@router.post("/recruitment-runs/{run_id}/cancel", response_model=RecruitmentRunEnvelope)
async def cancel_recruitment_run(
    run_id: str,
    request_id: RequestIdDep,
    service: TaskServiceDep,
) -> RecruitmentRunEnvelope:
    """Cancel a recruitment run in the MVP run store."""
    return RecruitmentRunEnvelope(
        request_id=request_id,
        run=_run_response(service.cancel_run(run_id)),
    )


def _run_response(run: RecruitmentRunRecord) -> RecruitmentRunResponse:
    return RecruitmentRunResponse(
        run_id=run.run_id,
        task_id=run.task_id,
        thread_id=run.thread_id,
        status=run.status,
        error_code=run.error_code,
        node_trace=list(run.node_trace),
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


def _sse_lines(
    events: Iterable[RecruitmentRunEventRecord],
    *,
    request_id: str,
) -> Iterable[str]:
    for event in events:
        payload = RecruitmentRunEventPayload(
            event_id=event.event_id,
            request_id=request_id,
            run_id=event.run_id,
            sequence=event.sequence,
            timestamp=event.timestamp,
            payload=event.payload,
        )
        yield f"event: {event.event_type}\n"
        yield f"data: {_json(payload.model_dump())}\n\n"


def _json(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
