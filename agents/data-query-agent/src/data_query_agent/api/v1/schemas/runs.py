"""Run API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from data_query_agent.domain.entities.run import QueryRun


class RunCreateRequest(BaseModel):
    """Request body for creating a query run under a thread."""

    question: str = Field(min_length=1, max_length=2000)
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=32)
    channel: Literal["web", "feishu"] = "web"
    idempotency_key: str | None = Field(default=None, max_length=128)


class RunResponse(BaseModel):
    """Public run DTO returned after creation."""

    run_id: str
    thread_id: str
    status: str
    question: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_entity(cls, *, run: QueryRun, thread_public_id: str, question: str) -> RunResponse:
        """Convert a run entity to a public response DTO."""
        return cls(
            run_id=run.public_id,
            thread_id=thread_public_id,
            status=run.status.value,
            question=question,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )


class RunDataEnvelope(BaseModel):
    """Success envelope for one run."""

    data: RunResponse
    error: None = None


class ErrorEnvelope(BaseModel):
    """OpenAPI error envelope shape."""

    data: None = None
    error: dict[str, Any]
