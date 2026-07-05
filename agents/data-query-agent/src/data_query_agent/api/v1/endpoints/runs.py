"""Run creation endpoints for data-query workflow requests."""

from __future__ import annotations

from fastapi import APIRouter

from data_query_agent.api.dependencies import (
    CurrentSubjectDep,
    IdentityThreadServiceDep,
    QueryRunTraceServiceDep,
)
from data_query_agent.api.v1.schemas.runs import RunCreateRequest, RunDataEnvelope, RunResponse
from data_query_agent.core.errors import NotFoundError
from data_query_agent.domain.entities.identity import MessageRole

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
