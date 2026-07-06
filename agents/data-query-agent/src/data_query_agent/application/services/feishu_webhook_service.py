"""Application service: verify/decrypt/dedupe a Feishu webhook into a result.

把飞书回调的安全边界（验签 → 解密 → token 校验 → 去重 → 解析）收敛到应用层，
让 api 路由保持轻薄。仅依赖 infrastructure adapter 与 bot service，可离线测试。
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from data_query_agent.application.services.feishu_bot_service import (
    FeishuInboundMessage,
    parse_message_event,
)
from data_query_agent.core.errors import ForbiddenError, InputBlockedError
from data_query_agent.infrastructure.integrations.feishu_event_dedup import FeishuEventDedupStore
from data_query_agent.infrastructure.integrations.feishu_signature import (
    decrypt_event,
    verify_event_signature,
    verify_verification_token,
)

_MESSAGE_EVENT_TYPE = "im.message.receive_v1"
_URL_VERIFICATION_TYPE = "url_verification"


@dataclass(frozen=True, slots=True)
class FeishuWebhookResult:
    """Outcome of processing one webhook request."""

    challenge: str | None
    message: FeishuInboundMessage | None


class FeishuWebhookProcessor:
    """Verify, decrypt and classify one Feishu webhook request."""

    def __init__(
        self,
        *,
        encrypt_key: str,
        verification_token: str,
        dedup: FeishuEventDedupStore,
    ) -> None:
        self._encrypt_key = encrypt_key
        self._verification_token = verification_token
        self._dedup = dedup

    async def process(
        self,
        *,
        raw_body: bytes,
        timestamp: str | None,
        nonce: str | None,
        signature: str | None,
    ) -> FeishuWebhookResult:
        """Return a challenge, a message to answer, or an ignored result."""
        event = self._decode_event(
            raw_body=raw_body, timestamp=timestamp, nonce=nonce, signature=signature
        )
        if event.get("type") == _URL_VERIFICATION_TYPE:
            return self._handle_url_verification(event)

        header = event.get("header")
        header_map = header if isinstance(header, dict) else {}
        verify_verification_token(
            event_token=str(header_map.get("token", "")), expected=self._verification_token
        )
        if header_map.get("event_type") != _MESSAGE_EVENT_TYPE:
            return FeishuWebhookResult(challenge=None, message=None)

        event_id = header_map.get("event_id")
        if isinstance(event_id, str) and await self._dedup.is_duplicate(event_id):
            return FeishuWebhookResult(challenge=None, message=None)

        return FeishuWebhookResult(challenge=None, message=parse_message_event(event))

    def _decode_event(
        self,
        *,
        raw_body: bytes,
        timestamp: str | None,
        nonce: str | None,
        signature: str | None,
    ) -> dict[str, object]:
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise InputBlockedError("Feishu webhook body is not valid JSON") from exc
        if not isinstance(data, dict):
            raise InputBlockedError("Feishu webhook body must be a JSON object")
        if "encrypt" not in data:
            return data
        if not self._encrypt_key:
            raise ForbiddenError("encrypted Feishu event received but no encrypt key configured")
        verify_event_signature(
            timestamp=timestamp or "",
            nonce=nonce or "",
            encrypt_key=self._encrypt_key,
            body=raw_body,
            signature=signature or "",
        )
        return decrypt_event(encrypt=str(data["encrypt"]), encrypt_key=self._encrypt_key)

    def _handle_url_verification(self, event: dict[str, object]) -> FeishuWebhookResult:
        verify_verification_token(
            event_token=str(event.get("token", "")), expected=self._verification_token
        )
        challenge = event.get("challenge")
        if not isinstance(challenge, str) or not challenge:
            raise InputBlockedError("Feishu url_verification challenge is required")
        return FeishuWebhookResult(challenge=challenge, message=None)


@dataclass(frozen=True, slots=True)
class FeishuWebhookDeps:
    """Assembled per-request collaborators for the webhook route."""

    enabled: bool
    processor: FeishuWebhookProcessor | None
    dispatch: Callable[[FeishuInboundMessage], Awaitable[None]] | None
