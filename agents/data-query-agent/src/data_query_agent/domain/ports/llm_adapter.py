"""Port for structured LLM completion adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


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


class LlmAdapter(Protocol):
    """Boundary for model providers that return structured text only."""

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        """Return a completion for a rendered prompt without executing it."""
