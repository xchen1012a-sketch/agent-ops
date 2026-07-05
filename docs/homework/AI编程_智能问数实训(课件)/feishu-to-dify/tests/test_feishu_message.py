"""Unit tests for Feishu message parsing."""

from app.models.schemas import CardStreamSession
from app.services.feishu_message import (
    build_dify_user_id,
    extract_user_text,
    parse_from_event_dict,
    truncate_utf8,
)


def test_parse_from_event_dict_text() -> None:
    event = {
        "sender": {
            "sender_id": {"open_id": "ou_abc", "user_id": "u1"},
            "sender_type": "user",
        },
        "message": {
            "message_id": "om_123",
            "chat_id": "oc_chat",
            "chat_type": "group",
            "message_type": "text",
            "content": '{"text": "@_user_1 hello world"}',
        },
    }
    message = parse_from_event_dict(event)
    assert message is not None
    assert message.message_id == "om_123"
    assert message.open_id == "ou_abc"
    assert extract_user_text(message) == "hello world"


def test_build_dify_user_id() -> None:
    event = {
        "sender": {"sender_id": {"open_id": "ou_x"}, "sender_type": "user"},
        "message": {
            "message_id": "m1",
            "chat_id": "oc_y",
            "message_type": "text",
            "content": '{"text": "hi"}',
        },
    }
    message = parse_from_event_dict(event)
    assert message is not None
    assert build_dify_user_id(message) == "feishu_ou_x_oc_y"


def test_card_stream_session_sequence() -> None:
    session = CardStreamSession(card_id="c1")
    assert session.next_sequence() == 1
    assert session.next_sequence() == 2


def test_truncate_utf8() -> None:
    text = "a" * 40000
    truncated = truncate_utf8(text, max_bytes=100)
    assert len(truncated.encode("utf-8")) <= 100
