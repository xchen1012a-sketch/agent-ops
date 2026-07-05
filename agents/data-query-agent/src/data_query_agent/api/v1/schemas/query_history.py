"""Query history API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from data_query_agent.domain.entities.run import QueryRun


class QueryHistoryItem(BaseModel):
    """Public query-history item that never exposes generated SQL."""

    query_id: str
    status: str
    error_code: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_entity(cls, run: QueryRun) -> QueryHistoryItem:
        """Convert a run entity to a public history item."""
        return cls(
            query_id=run.public_id,
            status=run.status.value,
            error_code=run.error_code,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )


class QueryHistoryListData(BaseModel):
    """Paginated query history payload."""

    items: list[QueryHistoryItem]
    limit: int
    offset: int


class QueryHistoryListEnvelope(BaseModel):
    """Success envelope for query history list."""

    data: QueryHistoryListData
    error: None = None


class QueryHistoryDetailEnvelope(BaseModel):
    """Success envelope for query history detail."""

    data: QueryHistoryItem
    error: None = None


class ErrorEnvelope(BaseModel):
    """OpenAPI error envelope shape."""

    data: None = None
    error: dict[str, Any]
