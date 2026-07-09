"""End-to-end mock Feishu flow for data-query agent semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from data_query_agent.core.errors import InputBlockedError
from data_query_agent.infrastructure.integrations.feishu_cards import (
    FeishuCardProjection,
    FeishuCardProjectionService,
)
from data_query_agent.infrastructure.integrations.feishu_events import (
    FeishuEventResult,
    FeishuMockEventService,
)
from data_query_agent.workflows.graph import create_data_query_graph


@dataclass(frozen=True, slots=True)
class FeishuMockFlowResult:
    """End-to-end mock Feishu flow result."""

    event: FeishuEventResult
    card: FeishuCardProjection | None


class FeishuMockFlowService:
    """Run mock Feishu message events through data-query workflow semantics."""

    def __init__(
        self,
        *,
        event_service: FeishuMockEventService | None = None,
        card_service: FeishuCardProjectionService | None = None,
    ) -> None:
        self._event_service = event_service or FeishuMockEventService()
        self._card_service = card_service or FeishuCardProjectionService()

    async def handle_event(
        self,
        *,
        payload: dict[str, Any],
        signature: str | None,
    ) -> FeishuMockFlowResult:
        """Handle challenge/message fixtures without real Feishu network calls."""
        event = await self._event_service.handle_event(payload=payload, signature=signature)
        if event.event_type == "challenge" or event.duplicate:
            return FeishuMockFlowResult(event=event, card=None)
        question = _extract_message_text(payload)
        graph = cast(Any, create_data_query_graph())
        state = graph.invoke({"question": question})
        card = self._card_service.project(
            answer=str(state.get("answer", "")),
            query_result=_dict_or_none(state.get("query_result")),
            chart=_dict_or_none(state.get("chart")),
            followups=tuple(item for item in state.get("followups", ()) if isinstance(item, str)),
        )
        return FeishuMockFlowResult(event=event, card=card)


def _extract_message_text(payload: dict[str, Any]) -> str:
    event = payload.get("event")
    if not isinstance(event, dict):
        raise InputBlockedError("Feishu message event body is required")
    message = event.get("message")
    if not isinstance(message, dict):
        raise InputBlockedError("Feishu message payload is required")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise InputBlockedError("Feishu message content is required")
    return content.strip()


def _dict_or_none(value: object) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None
