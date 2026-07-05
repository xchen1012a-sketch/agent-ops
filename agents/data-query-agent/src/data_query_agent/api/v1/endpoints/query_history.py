"""Query history endpoints for user-owned run summaries."""

from __future__ import annotations

from fastapi import APIRouter, Query

from data_query_agent.api.dependencies import (
    CurrentSubjectDep,
    IdentityThreadServiceDep,
    QueryRunTraceServiceDep,
)
from data_query_agent.api.v1.schemas.query_history import (
    QueryHistoryDetailEnvelope,
    QueryHistoryItem,
    QueryHistoryListData,
    QueryHistoryListEnvelope,
)
from data_query_agent.core.errors import NotFoundError

router = APIRouter()


@router.get("/query-history", response_model=QueryHistoryListEnvelope)
async def list_query_history(
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> QueryHistoryListEnvelope:
    """List current user's query run summaries without SQL exposure."""
    user = await identity_service.get_user_for_subject(external_subject=subject)
    if user is None or user.id is None:
        return QueryHistoryListEnvelope(
            data=QueryHistoryListData(items=[], limit=limit, offset=offset)
        )
    runs = await run_trace_service.list_runs_for_user(user_id=user.id, limit=limit, offset=offset)
    return QueryHistoryListEnvelope(
        data=QueryHistoryListData(
            items=[QueryHistoryItem.from_entity(run) for run in runs],
            limit=limit,
            offset=offset,
        )
    )


@router.get("/query-history/{query_id}", response_model=QueryHistoryDetailEnvelope)
async def get_query_history(
    query_id: str,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> QueryHistoryDetailEnvelope:
    """Return a current-user query summary by public run id."""
    user = await identity_service.get_user_for_subject(external_subject=subject)
    if user is None or user.id is None:
        raise NotFoundError("query history not found")
    run = await run_trace_service.get_run_for_user(run_public_id=query_id, user_id=user.id)
    if run is None:
        raise NotFoundError("query history not found")
    return QueryHistoryDetailEnvelope(data=QueryHistoryItem.from_entity(run))
