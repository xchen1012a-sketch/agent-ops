"""Prompt-backed high-risk assessment service with injectable LLM adapter."""

from __future__ import annotations

from collections.abc import Callable, Sequence
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
)

RISK_CHECK_VALIDATION_FAILED_REASON = "risk_check_validation_failed"


@dataclass(frozen=True, slots=True)
class LegalRiskCheckResult:
    """Structured risk assessment result used by the workflow state."""

    high_risk: bool
    risk_reason: str | None


class LegalRiskCheckPromptService:
    """Assess high-risk content through prompt rendering and output validation."""

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

    def assess(
        self,
        *,
        question: str,
        answer: str,
        citations: Sequence[Citation],
        category: str | None,
    ) -> LegalRiskCheckResult:
        """Render risk prompt, call adapter, and validate structured output."""

        rendered = self._template_loader.render(
            prompt=self._prompt,
            variables={
                "question": question,
                "answer": answer,
                "citations": list(citations),
                "category": category or "other",
            },
        )
        raw_output = self._llm_adapter.complete(rendered.content)
        validated = self._output_validator.validate_json(
            prompt=self._prompt,
            raw_output=raw_output,
        )
        high_risk = validated.data["high_risk"]
        if not isinstance(high_risk, bool):
            raise PromptOutputValidationError("risk_check high_risk must be a boolean")
        risk_reason = _optional_reason(validated.data.get("risk_reason"))
        if high_risk and risk_reason is None:
            raise PromptOutputValidationError("risk_check risk_reason is required for high risk")
        return LegalRiskCheckResult(high_risk=high_risk, risk_reason=risk_reason)


def _optional_reason(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PromptOutputValidationError("risk_check risk_reason must be a string or null")
    stripped = value.strip()
    return stripped or None


def make_prompt_risk_check_node(
    service: LegalRiskCheckPromptService,
) -> Callable[[LegalWorkflowState], LegalWorkflowUpdate]:
    """Build a workflow node that consumes the prompt-backed risk check service."""

    def prompt_risk_check_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
        if state.get("error_code"):
            return {"node_trace": [*state.get("node_trace", []), "risk_check"]}
        try:
            result = service.assess(
                question=state.get("safe_question") or "",
                answer=state.get("validated_answer") or state.get("answer_draft") or "",
                citations=state.get("citations", []),
                category=state.get("category"),
            )
        except (PromptOutputValidationError, ValueError):
            return {
                "high_risk": True,
                "risk_reason": RISK_CHECK_VALIDATION_FAILED_REASON,
                "node_trace": [*state.get("node_trace", []), "risk_check"],
            }
        return {
            "high_risk": result.high_risk,
            "risk_reason": result.risk_reason,
            "node_trace": [*state.get("node_trace", []), "risk_check"],
        }

    return prompt_risk_check_node
