"""Unit tests for end-to-end mock Feishu flow."""

from __future__ import annotations

import pytest

from data_query_agent.core.errors import InputBlockedError
from data_query_agent.infrastructure.integrations.feishu_events import MOCK_FEISHU_SIGNATURE
from data_query_agent.infrastructure.integrations.feishu_flow import FeishuMockFlowService


@pytest.mark.asyncio
async def test_feishu_mock_flow_returns_challenge_without_card() -> None:
    result = await FeishuMockFlowService().handle_event(
        payload={"type": "url_verification", "challenge": "challenge-token"},
        signature=MOCK_FEISHU_SIGNATURE,
    )

    assert result.event.event_type == "challenge"
    assert result.event.challenge == "challenge-token"
    assert result.card is None


@pytest.mark.asyncio
async def test_feishu_mock_flow_reuses_data_query_workflow_and_card_projection() -> None:
    service = FeishuMockFlowService()

    result = await service.handle_event(
        payload={
            "type": "message",
            "header": {"event_id": "evt-sales"},
            "event": {"message": {"content": "What are total sales this month?"}},
        },
        signature=MOCK_FEISHU_SIGNATURE,
    )

    assert result.event.event_type == "message"
    assert result.event.duplicate is False
    assert result.card is not None
    assert result.card.card_type == "table"
    assert result.card.elements[0] == {"type": "markdown", "content": "Query result is 98765.43."}
    assert result.card.elements[1]["columns"] == ("total_sales",)
    assert result.card.actions


@pytest.mark.asyncio
async def test_feishu_mock_flow_deduplicates_before_workflow_execution() -> None:
    service = FeishuMockFlowService()
    payload = {
        "type": "message",
        "header": {"event_id": "evt-duplicate"},
        "event": {"message": {"content": "What are total sales this month?"}},
    }

    first = await service.handle_event(payload=payload, signature=MOCK_FEISHU_SIGNATURE)
    second = await service.handle_event(payload=payload, signature=MOCK_FEISHU_SIGNATURE)

    assert first.event.duplicate is False
    assert first.card is not None
    assert second.event.duplicate is True
    assert second.card is None


@pytest.mark.asyncio
async def test_feishu_mock_flow_rejects_message_without_content() -> None:
    with pytest.raises(InputBlockedError):
        await FeishuMockFlowService().handle_event(
            payload={"type": "message", "header": {"event_id": "evt-bad"}, "event": {}},
            signature=MOCK_FEISHU_SIGNATURE,
        )
