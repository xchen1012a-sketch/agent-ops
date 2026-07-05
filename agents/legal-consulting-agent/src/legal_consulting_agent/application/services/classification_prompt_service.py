"""Prompt-backed classification service with injectable LLM adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.prompts import (
    PromptOutputValidationError,
    PromptOutputValidator,
    PromptTemplateLoader,
)
from legal_consulting_agent.workflows.legal_state import (
    LegalEntityHints,
    LegalWorkflowState,
    LegalWorkflowUpdate,
)


class TextLLMAdapter(Protocol):
    """Minimal text completion adapter contract for mock and real LLMs."""

    def complete(self, prompt: str) -> str:
        """Return raw model text for a rendered prompt."""


@dataclass(frozen=True, slots=True)
class LegalClassificationResult:
    """Structured classification result used by the workflow state."""

    category: str
    intent: str
    legal_entities: LegalEntityHints


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _entity_hints(value: object) -> LegalEntityHints:
    if not isinstance(value, Mapping):
        return {}
    return {
        "statute_numbers": _string_list(value.get("statute_numbers")),
        "statute_names": _string_list(value.get("statute_names")),
        "case_keywords": _string_list(value.get("case_keywords")),
    }


class LegalClassificationPromptService:
    """Classify a safe legal question through prompt rendering and output validation."""

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

    def classify(self, question: str) -> LegalClassificationResult:
        """Render classification prompt, call adapter, and validate structured output."""

        rendered = self._template_loader.render(
            prompt=self._prompt,
            variables={"question": question},
        )
        raw_output = self._llm_adapter.complete(rendered.content)
        validated = self._output_validator.validate_json(
            prompt=self._prompt,
            raw_output=raw_output,
        )
        category = validated.data["category"]
        intent = validated.data["intent"]
        if not isinstance(category, str) or not isinstance(intent, str):
            raise PromptOutputValidationError("classification output fields must be strings")
        return LegalClassificationResult(
            category=category,
            intent=intent,
            legal_entities=_entity_hints(validated.data.get("legal_entities")),
        )


def make_prompt_classification_node(
    service: LegalClassificationPromptService,
) -> Callable[[LegalWorkflowState], LegalWorkflowUpdate]:
    """Build a workflow node that consumes the prompt-backed classification service."""

    def prompt_classification_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
        if not state.get("is_safe", False):
            return {"node_trace": [*state.get("node_trace", []), "classification"]}
        try:
            result = service.classify(state.get("safe_question") or "")
        except (PromptOutputValidationError, ValueError):
            return {
                "category": "other",
                "intent": "分类失败，降级为 other",
                "legal_entities": {},
                "error_code": "CLASSIFY_FAILED",
                "node_trace": [*state.get("node_trace", []), "classification"],
            }
        return {
            "category": result.category,
            "intent": result.intent,
            "legal_entities": result.legal_entities,
            "node_trace": [*state.get("node_trace", []), "classification"],
        }

    return prompt_classification_node
