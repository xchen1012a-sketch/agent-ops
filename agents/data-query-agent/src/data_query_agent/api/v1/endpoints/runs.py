"""Run creation endpoints for data-query workflow requests."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from data_query_agent.api.dependencies import (
    CurrentSubjectDep,
    IdentityThreadServiceDep,
    QueryRunTraceServiceDep,
)
from data_query_agent.api.v1.schemas.runs import (
    RunCreateRequest,
    RunDataEnvelope,
    RunDetailEnvelope,
    RunDetailResponse,
    RunResponse,
)
from data_query_agent.core.errors import NotFoundError
from data_query_agent.domain.entities.identity import MessageRole
from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus

router = APIRouter()


@router.post("/threads/{thread_id}/runs", response_model=RunDataEnvelope, status_code=201)
async def create_run(
    thread_id: str,
    payload: RunCreateRequest,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> RunDataEnvelope:
    """Create a pending run and user question message without executing workflow."""
    thread = await identity_service.get_owned_thread(
        thread_public_id=thread_id,
        external_subject=subject,
    )
    if thread is None:
        raise NotFoundError("thread not found")
    message = await identity_service.create_message_for_subject(
        external_subject=subject,
        thread_public_id=thread_id,
        role=MessageRole.USER,
        content=payload.question,
    )
    run = await run_trace_service.create_run_for_thread(
        thread=thread,
        question_message_id=message.id,
    )
    return RunDataEnvelope(
        data=RunResponse.from_entity(
            run=run,
            thread_public_id=thread.public_id,
            question=payload.question,
        )
    )


@router.get("/runs/{run_id}", response_model=RunDetailEnvelope)
async def get_run(
    run_id: str,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> RunDetailEnvelope:
    """Return run status projection without exposing generated SQL."""
    run = await _get_owned_run(
        run_id=run_id,
        subject=subject,
        identity_service=identity_service,
        run_trace_service=run_trace_service,
    )
    return RunDetailEnvelope(data=RunDetailResponse.from_entity(run))


@router.get("/runs/{run_id}/stream")
async def stream_run_events(
    run_id: str,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> StreamingResponse:
    """Stream run/node status events as an SSE contract projection."""
    run = await _get_owned_run(
        run_id=run_id,
        subject=subject,
        identity_service=identity_service,
        run_trace_service=run_trace_service,
    )
    node_runs = await run_trace_service.list_node_runs(run=run)
    return StreamingResponse(
        _iter_run_events(run=run, node_runs=tuple(node_runs)),
        media_type="text/event-stream",
    )


async def _get_owned_run(
    *,
    run_id: str,
    subject: str,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> QueryRun:
    user = await identity_service.get_user_for_subject(external_subject=subject)
    if user is None or user.id is None:
        raise NotFoundError("run not found")
    run = await run_trace_service.get_run_for_user(run_public_id=run_id, user_id=user.id)
    if run is None:
        raise NotFoundError("run not found")
    return run


async def _iter_run_events(*, run: QueryRun, node_runs: tuple[NodeRun, ...]) -> AsyncIterator[str]:
    if run.started_at is not None or run.status in {
        RunStatus.RUNNING,
        RunStatus.SUCCESS,
        RunStatus.FAILED,
    }:
        yield _sse_event("run.started", {"run_id": run.public_id, "status": run.status.value})
    for node_run in node_runs:
        if node_run.started_at is not None or node_run.status in {
            NodeStatus.RUNNING,
            NodeStatus.SUCCESS,
            NodeStatus.FAILED,
            NodeStatus.SKIPPED,
        }:
            yield _sse_event(
                "node.started",
                {
                    "run_id": run.public_id,
                    "node_name": node_run.node_name,
                    "attempt": node_run.attempt,
                },
            )
        if node_run.status in {NodeStatus.SUCCESS, NodeStatus.SKIPPED}:
            yield _sse_event(
                "node.completed",
                {
                    "run_id": run.public_id,
                    "node_name": node_run.node_name,
                    "status": node_run.status.value,
                    "attempt": node_run.attempt,
                },
            )
        if node_run.status is NodeStatus.FAILED:
            yield _sse_event(
                "node.failed",
                {
                    "run_id": run.public_id,
                    "node_name": node_run.node_name,
                    "error_code": node_run.error_code,
                    "attempt": node_run.attempt,
                },
            )
    if run.status is RunStatus.SUCCESS:
        yield _sse_event("run.completed", {"run_id": run.public_id, "status": run.status.value})
    if run.status is RunStatus.FAILED:
        yield _sse_event(
            "run.failed",
            {
                "run_id": run.public_id,
                "status": run.status.value,
                "error_code": run.error_code,
            },
        )


def _sse_event(event_name: str, payload: dict[str, object]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
