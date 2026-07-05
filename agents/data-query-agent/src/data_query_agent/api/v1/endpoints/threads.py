"""Thread endpoints for data-query conversations."""

from __future__ import annotations

from fastapi import APIRouter, Query

from data_query_agent.api.dependencies import CurrentSubjectDep, IdentityThreadServiceDep
from data_query_agent.api.v1.schemas.threads import (
    ThreadCreateRequest,
    ThreadDataEnvelope,
    ThreadListData,
    ThreadListEnvelope,
    ThreadResponse,
)
from data_query_agent.core.errors import NotFoundError

router = APIRouter()


@router.post("", response_model=ThreadDataEnvelope, status_code=201)
async def create_thread(
    payload: ThreadCreateRequest,
    subject: CurrentSubjectDep,
    service: IdentityThreadServiceDep,
) -> ThreadDataEnvelope:
    """Create a thread owned by the current authenticated subject."""
    thread = await service.create_thread_for_subject(
        external_subject=subject,
        title=payload.title,
    )
    return ThreadDataEnvelope(data=ThreadResponse.from_entity(thread))


@router.get("", response_model=ThreadListEnvelope)
async def list_threads(
    subject: CurrentSubjectDep,
    service: IdentityThreadServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ThreadListEnvelope:
    """List threads owned by the current authenticated subject."""
    threads = await service.list_owned_threads(
        external_subject=subject,
        limit=limit,
        offset=offset,
    )
    return ThreadListEnvelope(
        data=ThreadListData(
            items=[ThreadResponse.from_entity(thread) for thread in threads],
            limit=limit,
            offset=offset,
        )
    )


@router.get("/{thread_id}", response_model=ThreadDataEnvelope)
async def get_thread(
    thread_id: str,
    subject: CurrentSubjectDep,
    service: IdentityThreadServiceDep,
) -> ThreadDataEnvelope:
    """Return a thread only when it belongs to the current subject."""
    thread = await service.get_owned_thread(
        thread_public_id=thread_id,
        external_subject=subject,
    )
    if thread is None:
        raise NotFoundError("thread not found")
    return ThreadDataEnvelope(data=ThreadResponse.from_entity(thread))
