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


class RunDetailResponse(BaseModel):
    """Public run detail DTO without SQL exposure."""

    run_id: str
    status: str
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    @classmethod
    def from_entity(cls, run: QueryRun) -> RunDetailResponse:
        """Convert a run entity to a public detail DTO."""
        return cls(
            run_id=run.public_id,
            status=run.status.value,
            error_code=run.error_code,
            error_message=run.error_message,
            started_at=run.started_at,
            finished_at=run.finished_at,
            created_at=run.created_at,
        )


class RunLocalDemoResponse(BaseModel):
    """Local deterministic data-query workflow projection for MVP evidence."""

    question: str
    source_status: str
    source_note: str
    fixture_case_id: str | None = None
    generated_sql: str | None = None
    policy_allowed: bool
    policy_error_code: str | None = None
    query_result: dict[str, Any] | None = None
    answer: str
    chart: dict[str, Any] | None = None
    followups: list[str] = Field(default_factory=list)
    node_trace: list[dict[str, str]] = Field(default_factory=list)

    @classmethod
    def from_state(cls, *, question: str, state: dict[str, Any]) -> RunLocalDemoResponse:
        """Convert workflow state to an API-safe local demo response."""
        generated_sql = _string_or_none(state.get("generated_sql"))
        fixture_case_id = _string_or_none(state.get("fixture_case_id"))
        source_status = (
            "local_deterministic_fixture"
            if fixture_case_id is not None
            else "local_deterministic_workflow"
            if generated_sql is not None
            else "local_boundary_reply"
        )
        return cls(
            question=question,
            source_status=source_status,
            source_note=(
                "本地确定性 MVP 证据，仅用于演示；当前结果不是实时 MySQL、"
                "真实 Dify 或真实飞书输出。"
            ),
            fixture_case_id=fixture_case_id,
            generated_sql=None,
            policy_allowed=bool(state.get("policy_allowed", False)),
            policy_error_code=_string_or_none(state.get("policy_error_code")),
            query_result=_dict_or_none(state.get("query_result")),
            answer=str(state.get("answer", "")),
            chart=_dict_or_none(state.get("chart")),
            followups=[item for item in state.get("followups", []) if isinstance(item, str)],
            node_trace=[
                {"node_name": str(item.get("node_name", "")), "status": str(item.get("status", ""))}
                for item in state.get("node_trace", [])
                if isinstance(item, dict)
            ],
        )


class RunDataEnvelope(BaseModel):
    """Success envelope for one run."""

    data: RunResponse
    error: None = None


class RunDetailEnvelope(BaseModel):
    """Success envelope for run detail."""

    data: RunDetailResponse
    error: None = None


class RunLocalDemoEnvelope(BaseModel):
    """Success envelope for local deterministic workflow evidence."""

    data: RunLocalDemoResponse
    error: None = None


class ErrorEnvelope(BaseModel):
    """OpenAPI error envelope shape."""

    data: None = None
    error: dict[str, Any]


def _dict_or_none(value: object) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
