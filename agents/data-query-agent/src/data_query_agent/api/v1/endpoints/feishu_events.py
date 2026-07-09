"""Mock Feishu event endpoints for data-query integration."""

from __future__ import annotations

from fastapi import APIRouter, Header

from data_query_agent.api.dependencies import FeishuMockEventServiceDep
from data_query_agent.api.v1.schemas.feishu_events import (
    FeishuEventEnvelope,
    FeishuEventRequest,
    FeishuEventResponse,
)

router = APIRouter()


@router.post("/integrations/feishu/events", response_model=FeishuEventEnvelope)
async def handle_feishu_event(
    payload: FeishuEventRequest,
    service: FeishuMockEventServiceDep,
    x_feishu_signature: str | None = Header(default=None),
) -> FeishuEventEnvelope:
    """Handle Feishu challenge/message fixtures with mock signature and dedupe."""
    result = await service.handle_event(
        payload=payload.model_dump(exclude_none=True),
        signature=x_feishu_signature,
    )
    return FeishuEventEnvelope(data=FeishuEventResponse.from_result(result))
