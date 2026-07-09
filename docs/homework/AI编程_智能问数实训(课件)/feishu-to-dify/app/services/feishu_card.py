"""CardKit streaming card helper for Feishu replies."""

from __future__ import annotations

from app.models.schemas import CardStreamSession
from app.services.feishu_api import FeishuApiClient
from app.services.feishu_message import MSG_THINKING, truncate_utf8
from app.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_ELEMENT_ID = "markdown_1"


class FeishuCardStreamer:
    """Create, send, and stream-update a CardKit card."""

    def __init__(self, api: FeishuApiClient) -> None:
        self._api = api

    async def start_stream(
        self,
        *,
        chat_id: str,
        placeholder: str = MSG_THINKING,
        title: str = "AI 助手",
    ) -> CardStreamSession:
        card_id = await self._api.create_streaming_card(
            initial_text=placeholder,
            title=title,
        )
        await self._api.send_card_message(chat_id=chat_id, card_id=card_id)
        logger.debug("feishu card stream started card_id={} chat_id={}", card_id, chat_id)
        return CardStreamSession(card_id=card_id, element_id=DEFAULT_ELEMENT_ID, sequence=0)

    async def push_content(self, session: CardStreamSession, content: str) -> None:
        safe = truncate_utf8(content)
        seq = session.next_sequence()
        await self._api.update_card_content(
            card_id=session.card_id,
            element_id=session.element_id,
            content=safe,
            sequence=seq,
        )

    async def finish(self, session: CardStreamSession, content: str) -> None:
        safe = truncate_utf8(content)
        seq = session.next_sequence()
        await self._api.update_card_content(
            card_id=session.card_id,
            element_id=session.element_id,
            content=safe,
            sequence=seq,
        )
        end_seq = session.next_sequence()
        await self._api.end_card_stream(card_id=session.card_id, sequence=end_seq)
