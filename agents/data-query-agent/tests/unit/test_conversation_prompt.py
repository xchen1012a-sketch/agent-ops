"""Unit tests for conversation prompt assembly."""

from __future__ import annotations

from datetime import datetime

from data_query_agent.application.services.conversation_prompt import (
    with_conversation_history,
)
from data_query_agent.domain.entities.identity import MessageRole, ThreadMessage


def _message(role: MessageRole, content: str, *, public_id: str = "m") -> ThreadMessage:
    return ThreadMessage(
        id=1,
        public_id=public_id,
        thread_id=1,
        user_id=1,
        role=role,
        content=content,
        created_at=datetime(2026, 7, 1),
    )


def test_returns_question_unchanged_when_history_empty() -> None:
    assert with_conversation_history("上周销售额?", []) == "上周销售额?"


def test_returns_question_unchanged_when_history_has_only_system_messages() -> None:
    history = [_message(MessageRole.SYSTEM, "system prompt")]
    assert with_conversation_history("hi", history) == "hi"


def test_prepends_user_assistant_turns_in_order() -> None:
    history = [
        _message(MessageRole.USER, "上周销售额?"),
        _message(MessageRole.ASSISTANT, "上周销售额 12,345 元。"),
    ]

    rendered = with_conversation_history("那退款率呢?", history)

    assert rendered.startswith("【历史对话】")
    assert "用户: 上周销售额?" in rendered
    assert "助手: 上周销售额 12,345 元。" in rendered
    assert rendered.index("用户: 上周销售额?") < rendered.index("助手: 上周销售额")
    assert rendered.endswith("那退款率呢?")
    assert "【当前问题】" in rendered


def test_truncates_overlong_assistant_turns() -> None:
    long_answer = "答" * 1200
    history = [_message(MessageRole.ASSISTANT, long_answer)]

    rendered = with_conversation_history("继续", history)

    assert "答" * 1200 not in rendered
    # truncated turn ends with ellipsis; the current question still comes last.
    assert "…" in rendered
    assert rendered.endswith("继续")
