"""Thread API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from data_query_agent.domain.entities.identity import QueryThread


class ThreadCreateRequest(BaseModel):
    """Request body for creating a query thread."""

    title: str | None = Field(default=None, max_length=200)


class ThreadResponse(BaseModel):
    """Public thread DTO returned by thread APIs."""

    thread_id: str
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, thread: QueryThread) -> ThreadResponse:
        """Convert a domain thread to a public response DTO."""
        return cls(
            thread_id=thread.public_id,
            title=thread.title,
            status=thread.status.value,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
        )


class ThreadDataEnvelope(BaseModel):
    """Success envelope for a single thread."""

    data: ThreadResponse
    error: None = None


class ThreadListData(BaseModel):
    """Paginated thread list payload."""

    items: list[ThreadResponse]
    limit: int
    offset: int


class ThreadListEnvelope(BaseModel):
    """Success envelope for thread list."""

    data: ThreadListData
    error: None = None


class ErrorEnvelope(BaseModel):
    """OpenAPI error envelope shape."""

    data: None = None
    error: dict[str, Any]
