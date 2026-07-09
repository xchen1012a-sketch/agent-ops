"""Unit tests for the model-agnostic SSE forwarding middleware (STREAM-100)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from legal_consulting_agent.domain.ports.llm_adapter import LlmStreamChunk, LlmStreamError
from legal_consulting_agent.infrastructure.sse import iter_llm_sse


async def _from_list(chunks: list[LlmStreamChunk]) -> AsyncIterator[LlmStreamChunk]:
    for chunk in chunks:
        yield chunk


async def _collect(source: AsyncIterator[str]) -> list[str]:
    return [frame async for frame in source]


def _events(frames: list[str]) -> list[str]:
    events: list[str] = []
    for frame in frames:
        for line in frame.splitlines():
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
    return events


def _data(frame: str) -> dict[str, object]:
    for line in frame.splitlines():
        if line.startswith("data:"):
            return json.loads(line.split(":", 1)[1].strip())
    raise AssertionError("frame has no data line")


async def test_thinking_then_answer_maps_two_channels_and_completes() -> None:
    frames = await _collect(
        iter_llm_sse(
            _from_list(
                [
                    LlmStreamChunk(kind="thinking", text="想一下"),
                    LlmStreamChunk(kind="answer", text="答案"),
                ]
            ),
            run_id="run-x",
        )
    )

    assert _events(frames) == [
        "run.started",
        "message.thinking.delta",
        "message.thinking.completed",
        "message.delta",
        "message.completed",
    ]
    assert _data(frames[-1])["content"] == "答案"


async def test_completed_extra_is_merged_into_terminal_event() -> None:
    frames = await _collect(
        iter_llm_sse(
            _from_list([LlmStreamChunk(kind="answer", text="hi")]),
            run_id="run-x",
            completed_extra={"answer": "hi", "high_risk": True},
        )
    )

    terminal = _data(frames[-1])
    assert terminal["answer"] == "hi"
    assert terminal["high_risk"] is True


async def test_stream_error_becomes_run_failed_and_stops() -> None:
    async def _failing() -> AsyncIterator[LlmStreamChunk]:
        yield LlmStreamChunk(kind="answer", text="partial")
        raise LlmStreamError("upstream down", error_code="LLM_TIMEOUT", retryable=True)

    frames = await _collect(iter_llm_sse(_failing(), run_id="run-x"))

    assert _events(frames) == ["run.started", "message.delta", "run.failed"]
    assert _data(frames[-1])["error_code"] == "LLM_TIMEOUT"
    assert "message.completed" not in "".join(frames)
