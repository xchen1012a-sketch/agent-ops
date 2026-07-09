"""Unit tests for MessageBridge with mocked Feishu card and Dify client."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from app.config import Settings
from app.models.schemas import CardStreamSession, DifyStreamEvent, FeishuIncomingMessage
from app.services.bridge import MessageBridge
from app.utils.dedup import MessageDeduper


class FakeCardStreamer:
    def __init__(self) -> None:
        self.starts: list[str] = []
        self.pushes: list[str] = []
        self.finishes: list[str] = []

    async def start_stream(self, *, chat_id: str, placeholder: str = "正在思考...") -> CardStreamSession:
        self.starts.append(chat_id)
        return CardStreamSession(card_id="card_test")

    async def push_content(self, session: CardStreamSession, content: str) -> None:
        self.pushes.append(content)

    async def finish(self, session: CardStreamSession, content: str) -> None:
        self.finishes.append(content)


class FakeDifyClient:
    async def run_stream(self, query: str, user: str) -> AsyncIterator[DifyStreamEvent]:
        yield DifyStreamEvent(event="text_chunk", data={"text": "Hello "})
        yield DifyStreamEvent(event="text_chunk", data={"text": "world"})
        yield DifyStreamEvent(
            event="workflow_finished",
            data={"status": "succeeded", "outputs": {"text": "Hello world"}},
        )


@pytest.mark.asyncio
async def test_bridge_runs_dify_and_finishes_card() -> None:
    settings = Settings(
        feishu_app_id="cli_test",
        feishu_app_secret="secret",
        dify_api_key="app-test",
        ws_stream_push_interval=0.0,
    )
    cards = FakeCardStreamer()
    bridge = MessageBridge(
        settings,
        deduper=MessageDeduper(60),
        dify_client=FakeDifyClient(),  # type: ignore[arg-type]
        card_streamer=cards,  # type: ignore[arg-type]
    )
    message = FeishuIncomingMessage(
        message_id="om_1",
        chat_id="oc_1",
        chat_type="p2p",
        message_type="text",
        content='{"text": "你好"}',
        open_id="ou_1",
    )

    await bridge.handle_ws_message(message)
    while bridge._tasks:
        await asyncio.gather(*list(bridge._tasks))

    assert cards.starts == ["oc_1"]
    assert cards.finishes[-1] == "Hello world"


@pytest.mark.asyncio
async def test_bridge_deduplicates_messages() -> None:
    settings = Settings(
        feishu_app_id="cli_test",
        feishu_app_secret="secret",
        dify_api_key="app-test",
    )
    cards = FakeCardStreamer()
    bridge = MessageBridge(
        settings,
        deduper=MessageDeduper(60),
        dify_client=FakeDifyClient(),  # type: ignore[arg-type]
        card_streamer=cards,  # type: ignore[arg-type]
    )
    message = FeishuIncomingMessage(
        message_id="om_dup",
        chat_id="oc_1",
        message_type="text",
        content='{"text": "hi"}',
        open_id="ou_1",
    )

    await bridge.handle_ws_message(message)
    await bridge.handle_ws_message(message)
    while bridge._tasks:
        await asyncio.gather(*list(bridge._tasks))

    assert len(cards.starts) == 1
