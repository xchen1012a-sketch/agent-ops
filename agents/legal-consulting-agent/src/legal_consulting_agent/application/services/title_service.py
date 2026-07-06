"""LLM-backed session title generation with a deterministic fallback."""

from __future__ import annotations

from legal_consulting_agent.domain.ports.llm_adapter import LlmAdapter, LlmCompletionRequest

_TITLE_PROMPT_NAME = "legal_session_title"
_TITLE_PROMPT_VERSION = "v1"
_MAX_TITLE_LENGTH = 24
_DEFAULT_TITLE = "法律咨询"
_STRIP_CHARS = " \t\r\n\"'`《》「」【】<>：:。.、,，!！?？"


class LegalTitleService:
    """Generate a short session title from the first exchange.

    Uses the account's resolved LLM adapter when available; on empty output or
    any adapter error it degrades to a deterministic title derived from the
    first question, so naming never blocks or fails the request.
    """

    def __init__(self, *, llm_adapter: LlmAdapter) -> None:
        self._llm_adapter = llm_adapter

    async def generate_title(self, *, first_question: str, answer: str | None = None) -> str:
        """Return a concise title; falls back to the question if the LLM can't help."""

        rendered = _build_prompt(first_question=first_question, answer=answer)
        try:
            response = await self._llm_adapter.complete(
                LlmCompletionRequest(
                    prompt_name=_TITLE_PROMPT_NAME,
                    version=_TITLE_PROMPT_VERSION,
                    rendered_prompt=rendered,
                )
            )
            title = _sanitize(response.content)
        except Exception:
            title = ""
        return title or _fallback(first_question)


def _build_prompt(*, first_question: str, answer: str | None) -> str:
    parts = [
        "为下面这段法律咨询起一个简洁标题，要求：",
        "- 不超过 12 个字，概括核心诉求；",
        "- 只输出标题本身，不要引号、标点或解释。",
        "",
        f"用户问题：{first_question.strip()}",
    ]
    if answer:
        parts.append(f"回答摘要：{answer.strip()[:120]}")
    return "\n".join(parts)


def _sanitize(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    cleaned = first_line.strip(_STRIP_CHARS)
    return cleaned[:_MAX_TITLE_LENGTH].strip()


def _fallback(first_question: str) -> str:
    source = first_question.strip().splitlines()[0] if first_question.strip() else ""
    cleaned = source.strip(_STRIP_CHARS)[:_MAX_TITLE_LENGTH].strip()
    return cleaned or _DEFAULT_TITLE
