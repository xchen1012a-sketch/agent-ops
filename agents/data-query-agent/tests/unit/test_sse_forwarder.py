"""Unit tests for the model-agnostic SSE forwarding middleware (STREAM-100)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from data_query_agent.domain.ports.llm_adapter import LlmStreamChunk, LlmStreamError
from data_query_agent.infrastructure.sse import iter_llm_sse


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
                    LlmStreamChunk(kind="answer", text="继续"),
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
        "message.delta",
        "message.completed",
    ]
    # sequence is strictly increasing and mirrored into each payload.
    sequences = [int(_data(frame)["sequence"]) for frame in frames]
    assert sequences == list(range(1, len(frames) + 1))
    assert _data(frames[-1])["content"] == "答案继续"


async def test_thinking_completed_emitted_once_with_duration() -> None:
    frames = await _collect(
        iter_llm_sse(
            _from_list(
                [
                    LlmStreamChunk(kind="thinking", text="a"),
                    LlmStreamChunk(kind="thinking", text="b"),
                    LlmStreamChunk(kind="answer", text="c"),
                ]
            ),
            run_id="run-x",
        )
    )

    completed = [frame for frame in frames if "message.thinking.completed" in frame]
    assert len(completed) == 1
    duration_ms = _data(completed[0])["duration_ms"]
    assert isinstance(duration_ms, int)
    assert duration_ms >= 0
    # cumulative_length accumulates within a channel.
    thinking_deltas = [_data(f) for f in frames if "message.thinking.delta" in f]
    assert [d["cumulative_length"] for d in thinking_deltas] == [1, 2]


async def test_answer_only_stream_skips_thinking_completed() -> None:
    frames = await _collect(
        iter_llm_sse(
            _from_list([LlmStreamChunk(kind="answer", text="hi")]),
            run_id="run-x",
        )
    )

    assert _events(frames) == ["run.started", "message.delta", "message.completed"]


async def test_stream_error_becomes_run_failed_and_stops() -> None:
    async def _failing() -> AsyncIterator[LlmStreamChunk]:
        yield LlmStreamChunk(kind="answer", text="partial")
        raise LlmStreamError("upstream down", error_code="LLM_TIMEOUT", retryable=True)

    frames = await _collect(iter_llm_sse(_failing(), run_id="run-x"))

    assert _events(frames) == ["run.started", "message.delta", "run.failed"]
    failed = _data(frames[-1])
    assert failed["error_code"] == "LLM_TIMEOUT"
    assert failed["retryable"] is True
    assert "message.completed" not in "".join(frames)


async def test_idle_gap_emits_heartbeat() -> None:
    async def _slow() -> AsyncIterator[LlmStreamChunk]:
        await asyncio.sleep(0.03)
        yield LlmStreamChunk(kind="answer", text="late")

    frames = await _collect(
        iter_llm_sse(_slow(), run_id="run-x", heartbeat_timeout_seconds=0.005)
    )

    assert "heartbeat" in _events(frames)
    assert _events(frames)[-1] == "message.completed"
