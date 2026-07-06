"""Port for structured LLM completion adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class LlmCompletionRequest:
    """Prompt completion request after template rendering."""

    prompt_name: str
    version: str
    rendered_prompt: str


@dataclass(frozen=True, slots=True)
class LlmCompletionResponse:
    """Raw structured output returned by an LLM adapter."""

    content: str


@dataclass(frozen=True, slots=True)
class LlmStreamChunk:
    """One normalized streaming fragment classified as thinking or answer.

    模型无关：具体模型的字段名（reasoning_content/content 等）在 adapter 内归一化为
    这两类，转发层只认 kind，不认任何厂商字段。
    """

    kind: Literal["thinking", "answer"]
    text: str


class LlmStreamError(Exception):
    """Raised by an adapter when a streaming completion fails mid-stream.

    携带安全的 error_code 与 retryable 标记，供转发层转成 run.failed 事件；
    不得携带密钥、完整 Prompt 或上游堆栈。
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "LLM_STREAM_ERROR",
        retryable: bool = True,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.retryable = retryable


class LlmAdapter(Protocol):
    """Boundary for model providers that return structured text only."""

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        """Return a completion for a rendered prompt without executing it."""

    def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        """Yield normalized thinking/answer chunks for a rendered prompt.

        默认不支持流式；仅实现流式的 adapter 覆盖此方法。非流式 adapter 保持默认，
        被误用于流式时快速失败而非静默降级。
        """
        raise NotImplementedError("streaming completion not supported by this adapter")
