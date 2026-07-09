"""Model-agnostic, business-agnostic SSE forwarding for LLM stream chunks.

STREAM-100 层2：把归一化后的 thinking/answer 分块（``LlmStreamChunk``）翻译成前后端
共享的 SSE 事件契约。这里只做协议翻译——不认任何模型字段、不含任何业务逻辑，任何
Agent 可原样复制使用。
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Mapping

from recruitment_assistant_agent.domain.ports.llm_adapter import LlmStreamChunk, LlmStreamError

_EVENT_RUN_STARTED = "run.started"
_EVENT_THINKING_DELTA = "message.thinking.delta"
_EVENT_THINKING_COMPLETED = "message.thinking.completed"
_EVENT_MESSAGE_DELTA = "message.delta"
_EVENT_MESSAGE_COMPLETED = "message.completed"
_EVENT_RUN_FAILED = "run.failed"
_EVENT_HEARTBEAT = "heartbeat"


def sse_frame(event: str, data: Mapping[str, object], *, sequence: int) -> str:
    """Format one SSE frame with an id, event name and JSON data line.

    ``sequence`` is embedded both as the SSE ``id`` (for Last-Event-ID resume)
    and inside the JSON payload so the frontend client can de-dupe events.
    """
    body = json.dumps({"sequence": sequence, **dict(data)}, ensure_ascii=False, separators=(",", ":"))
    return f"id: {sequence}\nevent: {event}\ndata: {body}\n\n"


async def iter_llm_sse(
    chunks: AsyncIterator[LlmStreamChunk],
    *,
    run_id: str,
    heartbeat_timeout_seconds: float | None = None,
    completed_extra: Mapping[str, object] | None = None,
) -> AsyncIterator[str]:
    """Translate normalized thinking/answer chunks into the SSE event contract.

    Emits ``run.started`` → any number of ``message.thinking.delta`` →
    ``message.thinking.completed`` (once, when the first answer chunk follows
    thinking) → ``message.delta`` → ``message.completed``. A ``LlmStreamError``
    mid-stream is surfaced as ``run.failed`` and terminates the stream. When
    ``heartbeat_timeout_seconds`` is set, an idle gap emits a ``heartbeat`` frame
    instead of hanging. ``completed_extra`` merges opaque, caller-owned metadata
    (e.g. citations, message ids) into the terminal ``message.completed`` payload;
    it stays business-agnostic here — the forwarder never inspects the keys.
    """
    sequence = 0

    def _emit(event: str, data: dict[str, object]) -> str:
        nonlocal sequence
        sequence += 1
        return sse_frame(event, data, sequence=sequence)

    yield _emit(_EVENT_RUN_STARTED, {"run_id": run_id})

    thinking_started_at: float | None = None
    thinking_completed = False
    thinking_length = 0
    answer_length = 0
    answer_parts: list[str] = []
    iterator = chunks.__aiter__()

    try:
        while True:
            try:
                if heartbeat_timeout_seconds is not None:
                    chunk = await asyncio.wait_for(
                        iterator.__anext__(), heartbeat_timeout_seconds
                    )
                else:
                    chunk = await iterator.__anext__()
            except StopAsyncIteration:
                break
            except TimeoutError:
                yield _emit(_EVENT_HEARTBEAT, {"run_id": run_id})
                continue

            if chunk.kind == "thinking":
                if thinking_started_at is None:
                    thinking_started_at = time.monotonic()
                thinking_length += len(chunk.text)
                yield _emit(
                    _EVENT_THINKING_DELTA,
                    {
                        "run_id": run_id,
                        "delta": chunk.text,
                        "cumulative_length": thinking_length,
                    },
                )
                continue

            if thinking_started_at is not None and not thinking_completed:
                duration_ms = int((time.monotonic() - thinking_started_at) * 1000)
                yield _emit(
                    _EVENT_THINKING_COMPLETED,
                    {"run_id": run_id, "duration_ms": duration_ms},
                )
                thinking_completed = True
            answer_length += len(chunk.text)
            answer_parts.append(chunk.text)
            yield _emit(
                _EVENT_MESSAGE_DELTA,
                {
                    "run_id": run_id,
                    "delta": chunk.text,
                    "cumulative_length": answer_length,
                },
            )
    except LlmStreamError as error:
        yield _emit(
            _EVENT_RUN_FAILED,
            {
                "run_id": run_id,
                "error_code": error.error_code,
                "message": str(error),
                "retryable": error.retryable,
            },
        )
        return

    completed_payload: dict[str, object] = {"run_id": run_id, "content": "".join(answer_parts)}
    if completed_extra is not None:
        completed_payload.update(completed_extra)
    yield _emit(_EVENT_MESSAGE_COMPLETED, completed_payload)
