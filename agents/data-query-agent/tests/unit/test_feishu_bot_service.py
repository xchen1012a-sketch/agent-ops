"""Unit tests for Feishu message parsing and bot answering orchestration."""

from __future__ import annotations

import json

import pytest

from data_query_agent.application.services.feishu_bot_service import (
    FeishuBotService,
    FeishuInboundMessage,
    feishu_subject,
    parse_message_event,
)
from data_query_agent.core.errors import InputBlockedError


class _RecordingSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send_text(
        self, *, receive_id: str, text: str, receive_id_type: str = "open_id"
    ) -> None:
        self.sent.append({"receive_id": receive_id, "text": text})


class _FakeGraph:
    def __init__(self, answer: str) -> None:
        self._answer = answer

    def invoke(self, state: dict[str, object]) -> dict[str, object]:
        return {"answer": self._answer, "question": state.get("question")}


def _message(*, text: str = "total sales", message_type: str = "text") -> FeishuInboundMessage:
    return FeishuInboundMessage(
        open_id="ou_123",
        text=text,
        message_type=message_type,
        chat_id="oc_1",
        event_id="evt-1",
    )


def _text_event(content_text: str) -> dict[str, object]:
    return {
        "header": {"event_id": "evt-1", "event_type": "im.message.receive_v1"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou_123"}},
            "message": {
                "chat_id": "oc_1",
                "message_type": "text",
                "content": json.dumps({"text": content_text}),
            },
        },
    }


def test_feishu_subject_prefixes_open_id() -> None:
    assert feishu_subject("ou_123") == "feishu:ou_123"


def test_parse_message_event_extracts_sender_and_text() -> None:
    parsed = parse_message_event(_text_event("total sales"))

    assert parsed.open_id == "ou_123"
    assert parsed.text == "total sales"
    assert parsed.message_type == "text"
    assert parsed.chat_id == "oc_1"
    assert parsed.event_id == "evt-1"


def test_parse_message_event_rejects_missing_open_id() -> None:
    event = _text_event("x")
    event["event"] = {"sender": {"sender_id": {}}, "message": {}}
    with pytest.raises(InputBlockedError):
        parse_message_event(event)


async def test_answer_message_runs_workflow_and_sends_answer() -> None:
    sender = _RecordingSender()
    service = FeishuBotService(client=sender, graph_factory=lambda: _FakeGraph("42 orders"))

    await service.answer_message(_message())

    assert sender.sent == [{"receive_id": "ou_123", "text": "42 orders"}]


async def test_answer_message_replies_fallback_on_non_text() -> None:
    sender = _RecordingSender()
    service = FeishuBotService(client=sender, graph_factory=lambda: _FakeGraph("ignored"))

    await service.answer_message(_message(text="", message_type="image"))

    assert sender.sent[0]["receive_id"] == "ou_123"
    assert "文本" in sender.sent[0]["text"]


async def test_answer_message_replies_error_when_workflow_raises() -> None:
    sender = _RecordingSender()

    def _boom() -> _FakeGraph:
        raise RuntimeError("workflow blew up")

    service = FeishuBotService(client=sender, graph_factory=_boom)

    await service.answer_message(_message())

    assert len(sender.sent) == 1
    assert "出错" in sender.sent[0]["text"]


async def test_answer_message_replies_fallback_on_empty_answer() -> None:
    sender = _RecordingSender()
    service = FeishuBotService(client=sender, graph_factory=lambda: _FakeGraph(""))

    await service.answer_message(_message())

    assert sender.sent[0]["text"] != ""
