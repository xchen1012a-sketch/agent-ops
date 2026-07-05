"""Factory for assembling prompt-backed legal workflow nodes."""

from __future__ import annotations

from dataclasses import dataclass

from legal_consulting_agent.application.services.classification_prompt_service import (
    LegalClassificationPromptService,
    TextLLMAdapter,
    make_prompt_classification_node,
)
from legal_consulting_agent.application.services.generation_prompt_service import (
    LegalGenerationPromptService,
    make_prompt_generation_node,
)
from legal_consulting_agent.application.services.risk_prompt_service import (
    LegalRiskCheckPromptService,
    make_prompt_risk_check_node,
)
from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from legal_consulting_agent.workflows import build_legal_workflow_graph


@dataclass(frozen=True, slots=True)
class LegalPromptWorkflowPrompts:
    """Prompt versions required to assemble prompt-backed workflow nodes."""

    classification: PromptVersion
    generation: PromptVersion
    risk_check: PromptVersion


class LegalPromptWorkflowFactory:
    """Build a legal workflow graph from explicit prompt versions and adapters."""

    def __init__(
        self,
        *,
        template_loader: PromptTemplateLoader,
        output_validator: PromptOutputValidator,
        llm_adapter: TextLLMAdapter,
    ) -> None:
        self._template_loader = template_loader
        self._output_validator = output_validator
        self._llm_adapter = llm_adapter

    def build_graph(self, prompts: LegalPromptWorkflowPrompts) -> object:
        """Assemble prompt-backed nodes without connecting real external services."""

        classification_service = LegalClassificationPromptService(
            prompt=prompts.classification,
            template_loader=self._template_loader,
            output_validator=self._output_validator,
            llm_adapter=self._llm_adapter,
        )
        generation_service = LegalGenerationPromptService(
            prompt=prompts.generation,
            template_loader=self._template_loader,
            output_validator=self._output_validator,
            llm_adapter=self._llm_adapter,
        )
        risk_check_service = LegalRiskCheckPromptService(
            prompt=prompts.risk_check,
            template_loader=self._template_loader,
            output_validator=self._output_validator,
            llm_adapter=self._llm_adapter,
        )
        return build_legal_workflow_graph(
            classification_handler=make_prompt_classification_node(classification_service),
            generation_handler=make_prompt_generation_node(generation_service),
            risk_check_handler=make_prompt_risk_check_node(risk_check_service),
        )
