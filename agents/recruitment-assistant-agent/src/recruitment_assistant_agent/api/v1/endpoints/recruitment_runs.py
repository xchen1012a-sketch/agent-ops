"""Recruitment run endpoints and MVP SSE stream."""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from recruitment_assistant_agent.api.dependencies import (
    RecruitmentStreamAdapterDep,
    RequestIdDep,
)
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
from recruitment_assistant_agent.domain.ports.llm_adapter import LlmCompletionRequest
from recruitment_assistant_agent.infrastructure.sse import iter_llm_sse

router = APIRouter()

_STREAM_PROMPT_NAME = "recruitment_analysis"
_STREAM_PROMPT_VERSION = "v1"

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


@router.post("/recruitment-tasks/{task_id}/runs/stream")
async def stream_recruitment_run_completion(
    task_id: str,
    payload: RecruitmentRunStartRequest,
    llm_adapter: RecruitmentStreamAdapterDep,
) -> StreamingResponse:
    """Stream a live thinking/answer analysis for a task as SSE.

    STREAM-100 阶段4：mock 垂直切片。经模型无关的 SSE 转发层，把 adapter 归一化的
    thinking/analysis 分块推给前端；本阶段不落库、不跑真实工作流。
    """
    request = LlmCompletionRequest(
        prompt_name=_STREAM_PROMPT_NAME,
        version=_STREAM_PROMPT_VERSION,
        rendered_prompt=f"task={task_id}; prompt={payload.prompt_version}",
    )
    run_id = f"run_{uuid.uuid4().hex}"
    return StreamingResponse(
        iter_llm_sse(llm_adapter.stream(request), run_id=run_id),
        media_type="text/event-stream",
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
