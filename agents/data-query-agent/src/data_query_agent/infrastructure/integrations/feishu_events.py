"""Mock Feishu event boundary for local data-query integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from data_query_agent.core.errors import ForbiddenError, InputBlockedError

MOCK_FEISHU_SIGNATURE = "mock-valid-signature"


@dataclass(frozen=True, slots=True)
class FeishuEventResult:
    """Result of handling a mock Feishu event."""

    event_id: str | None
    event_type: Literal["challenge", "message"]
    duplicate: bool
    challenge: str | None = None


class FeishuMockEventService:
    """Validate mock Feishu signatures and deduplicate event ids in memory."""

    def __init__(self) -> None:
        self._seen_event_ids: set[str] = set()

    async def handle_event(
        self,
        *,
        payload: dict[str, Any],
        signature: str | None,
    ) -> FeishuEventResult:
        """Handle challenge and message events without real tenant calls."""
        _verify_mock_signature(signature)
        event_type = payload.get("type")
        if event_type == "url_verification":
            challenge = payload.get("challenge")
            if not isinstance(challenge, str) or not challenge.strip():
                raise InputBlockedError("Feishu challenge is required")
            return FeishuEventResult(
                event_id=None,
                event_type="challenge",
                duplicate=False,
                challenge=challenge,
            )
        if event_type != "message":
            raise InputBlockedError("Unsupported Feishu event type")
        header = payload.get("header")
        if not isinstance(header, dict):
            raise InputBlockedError("Feishu event header is required")
        event_id = header.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise InputBlockedError("Feishu event_id is required")
        duplicate = event_id in self._seen_event_ids
        self._seen_event_ids.add(event_id)
        return FeishuEventResult(
            event_id=event_id,
            event_type="message",
            duplicate=duplicate,
        )


def _verify_mock_signature(signature: str | None) -> None:
    if signature != MOCK_FEISHU_SIGNATURE:
        raise ForbiddenError("invalid Feishu mock signature")
