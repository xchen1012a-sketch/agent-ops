"""Schemas for recruitment run API endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from recruitment_assistant_agent.domain.value_objects.recruit_enums import RunStatus


class RecruitmentRunStartRequest(BaseModel):
    prompt_version: str = Field(default="recruit_prompt:v1", min_length=1, max_length=80)
    workflow_version: str = Field(default="recruitment_workflow:v1", min_length=1, max_length=80)


class RecruitmentRunResponse(BaseModel):
    run_id: str
    task_id: str
    thread_id: str
    status: RunStatus
    error_code: str | None
    node_trace: list[str]
    created_at: datetime
    completed_at: datetime | None


class RecruitmentRunStartResponse(BaseModel):
    request_id: str
    run: RecruitmentRunResponse
    stream_url: str


class RecruitmentRunEnvelope(BaseModel):
    request_id: str
    run: RecruitmentRunResponse


class RecruitmentRunEventPayload(BaseModel):
    event_id: str
    request_id: str
    run_id: str
    sequence: int
    timestamp: datetime
    payload: dict[str, str]
