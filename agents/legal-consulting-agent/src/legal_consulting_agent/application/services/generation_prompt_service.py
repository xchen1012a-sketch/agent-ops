"""Prompt-backed answer generation service with injectable LLM adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from legal_consulting_agent.application.services.classification_prompt_service import TextLLMAdapter
from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.prompts import (
    PromptOutputValidationError,
    PromptOutputValidator,
    PromptTemplateLoader,
)
from legal_consulting_agent.workflows.legal_state import (
    Citation,
    LegalWorkflowState,
    LegalWorkflowUpdate,
    RetrievalChunk,
)


@dataclass(frozen=True, slots=True)
class LegalGenerationResult:
    """Structured generation result used by the workflow state."""

    answer: str
    citations: list[Citation]


def _citation_list(value: object) -> list[Citation]:
    if not isinstance(value, list):
        raise PromptOutputValidationError("generation citations must be a list")
    citations: list[Citation] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise PromptOutputValidationError("generation citation item must be an object")
        source = item.get("source")
        section = item.get("section")
        snippet = item.get("snippet")
        if (
            not isinstance(source, str)
            or not isinstance(section, str)
            or not isinstance(snippet, str)
        ):
            raise PromptOutputValidationError("generation citation fields must be strings")
        citations.append({"source": source, "section": section, "snippet": snippet})
    return citations


class LegalGenerationPromptService:
    """Generate an answer through prompt rendering and output validation."""

    def __init__(
        self,
        *,
        prompt: PromptVersion,
        template_loader: PromptTemplateLoader,
        output_validator: PromptOutputValidator,
        llm_adapter: TextLLMAdapter,
    ) -> None:
        self._prompt = prompt
        self._template_loader = template_loader
        self._output_validator = output_validator
        self._llm_adapter = llm_adapter

    def generate(
        self,
        *,
        question: str,
        context_messages: Sequence[Mapping[str, str]],
        chunks: Sequence[RetrievalChunk],
        category: str | None,
    ) -> LegalGenerationResult:
        """Render generation prompt, call adapter, and validate structured output."""

        rendered = self._template_loader.render(
            prompt=self._prompt,
            variables={
                "question": question,
                "context": list(context_messages),
                "chunks": list(chunks),
                "category": category or "other",
            },
        )
        raw_output = self._llm_adapter.complete(rendered.content)
        validated = self._output_validator.validate_json(
            prompt=self._prompt,
            raw_output=raw_output,
        )
        answer = validated.data["answer"]
        if not isinstance(answer, str):
            raise PromptOutputValidationError("generation answer must be a string")
        return LegalGenerationResult(
            answer=answer,
            citations=_citation_list(validated.data.get("citations")),
        )


def make_prompt_generation_node(
    service: LegalGenerationPromptService,
) -> Callable[[LegalWorkflowState], LegalWorkflowUpdate]:
    """Build a workflow node that consumes the prompt-backed generation service."""

    def prompt_generation_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
        if state.get("error_code"):
            return {"node_trace": [*state.get("node_trace", []), "generation"]}
        try:
            result = service.generate(
                question=state.get("safe_question") or "",
                context_messages=state.get("context_messages", []),
                chunks=state.get("chunks", []),
                category=state.get("category"),
            )
        except (PromptOutputValidationError, ValueError):
            return {
                "answer_draft": None,
                "citations": [],
                "error_code": "CITATION_INVALID",
                "node_trace": [*state.get("node_trace", []), "generation"],
            }
        return {
            "answer_draft": result.answer,
            "citations": result.citations,
            "node_trace": [*state.get("node_trace", []), "generation"],
        }

    return prompt_generation_node
