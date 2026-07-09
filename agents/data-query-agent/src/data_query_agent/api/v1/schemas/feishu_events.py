"""Mock Feishu event API schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from data_query_agent.infrastructure.integrations.feishu_events import FeishuEventResult


class FeishuEventRequest(BaseModel):
    """Loose Feishu event request body for mock integration boundary."""

    type: str = Field(min_length=1, max_length=64)
    challenge: str | None = Field(default=None, max_length=256)
    header: dict[str, Any] | None = None
    event: dict[str, Any] | None = None


class FeishuEventResponse(BaseModel):
    """Mock Feishu event response projection."""

    event_type: Literal["challenge", "message"]
    event_id: str | None
    duplicate: bool
    challenge: str | None

    @classmethod
    def from_result(cls, result: FeishuEventResult) -> FeishuEventResponse:
        """Convert a service result to API DTO."""
        return cls(
            event_type=result.event_type,
            event_id=result.event_id,
            duplicate=result.duplicate,
            challenge=result.challenge,
        )


class FeishuEventEnvelope(BaseModel):
    """Success envelope for mock Feishu events."""

    data: FeishuEventResponse
    error: None = None
