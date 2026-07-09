"""Conversation prompt assembly for multi-turn data-query.

The deterministic ``sql_generate_node`` only consumes ``state['question']`` and
``state['schema_context']``. To give the LLM multi-turn memory we fold prior
``user``/``assistant`` messages into the question string as a labelled context
block. This keeps the prompt template variables unchanged (no schema break)
while letting the model see what was already asked and answered in this thread.
"""

from __future__ import annotations

from collections.abc import Sequence

from data_query_agent.domain.entities.identity import MessageRole, ThreadMessage

_HISTORY_LIMIT_LABELS = {
    MessageRole.USER: "用户",
    MessageRole.ASSISTANT: "助手",
}


def with_conversation_history(question: str, history: Sequence[ThreadMessage]) -> str:
    """Prepend prior turns (oldest → newest) to the current question.

    Returns the original question unchanged when history is empty. Each turn is
    trimmed to a generous length so a long prior answer cannot crowd out the
    schema + question payload.
    """
    trimmed_history = [message for message in history if message.role in _HISTORY_LIMIT_LABELS]
    if not trimmed_history:
        return question

    lines: list[str] = ["【历史对话】"]
    for message in trimmed_history:
        label = _HISTORY_LIMIT_LABELS[message.role]
        content = (message.content or "").strip()
        if not content:
            continue
        lines.append(f"{label}: {_truncate(content, _MAX_TURN_CHARS)}")

    lines.append("【当前问题】")
    lines.append(question.strip())
    return "\n".join(lines)


_MAX_TURN_CHARS = 600


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
