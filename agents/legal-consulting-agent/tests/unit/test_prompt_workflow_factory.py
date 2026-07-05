"""Unit tests for assembling prompt-backed legal workflow graphs."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from legal_consulting_agent.application.services import (
    LegalPromptWorkflowFactory,
    LegalPromptWorkflowPrompts,
)
from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.domain.value_objects.legal_enums import PromptStatus
from legal_consulting_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState


class RoutingLLMAdapter:
    """Return deterministic JSON by prompt marker."""

    def complete(self, prompt: str) -> str:
        if "CLASSIFY" in prompt:
            return (
                '{"category":"civil_labor","intent":"labor contract dispute",'
                '"legal_entities":{"statute_numbers":[],"statute_names":[],"case_keywords":["transfer"]}}'
            )
        if "GENERATE" in prompt:
            return (
                '{"answer":"Review the labor contract and negotiate first.",'
                '"citations":[{"source":"Labor Contract Law","section":"Article 35",'
                '"snippet":"The employer and employee may modify the labor contract by consensus."}]}'
            )
        if "RISK" in prompt:
            return '{"high_risk":false,"risk_reason":null}'
        raise AssertionError(f"unexpected prompt: {prompt}")


def prompt_version(
    *,
    prompt_id: int,
    name: str,
    template_key: str,
    required: list[str],
    output_schema: dict[str, object],
) -> PromptVersion:
    return PromptVersion(
        id=prompt_id,
        prompt_name=name,
        version="v1",
        template_key=template_key,
        variables={"required": required},
        output_schema=output_schema,
        status=PromptStatus.ACTIVE,
        created_by=1,
    )


def write_template(root: Path, key: str, content: str) -> None:
    path = root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_templates(root: Path) -> None:
    write_template(root, "legal_classification/v1/template.txt", "CLASSIFY {question}")
    write_template(
        root,
        "legal_generation/v1/template.txt",
        "GENERATE {question} {context} {chunks} {category}",
    )
    write_template(
        root,
        "legal_risk_check/v1/template.txt",
        "RISK {question} {answer} {citations} {category}",
    )


def workflow_prompts() -> LegalPromptWorkflowPrompts:
    return LegalPromptWorkflowPrompts(
        classification=prompt_version(
            prompt_id=1,
            name="legal_classification",
            template_key="legal_classification/v1/template.txt",
            required=["question"],
            output_schema={
                "type": "object",
                "required": ["category", "intent", "legal_entities"],
                "properties": {
                    "category": {"type": "string"},
                    "intent": {"type": "string"},
                    "legal_entities": {"type": "object"},
                },
            },
        ),
        generation=prompt_version(
            prompt_id=2,
            name="legal_generation",
            template_key="legal_generation/v1/template.txt",
            required=["question", "context", "chunks", "category"],
            output_schema={
                "type": "object",
                "required": ["answer", "citations"],
                "properties": {
                    "answer": {"type": "string"},
                    "citations": {"type": "array"},
                },
            },
        ),
        risk_check=prompt_version(
            prompt_id=3,
            name="legal_risk_check",
            template_key="legal_risk_check/v1/template.txt",
            required=["question", "answer", "citations", "category"],
            output_schema={
                "type": "object",
                "required": ["high_risk", "risk_reason"],
                "properties": {
                    "high_risk": {"type": "boolean"},
                    "risk_reason": {"type": ["string", "null"]},
                },
            },
        ),
    )


def initial_state() -> LegalWorkflowState:
    chunks = [
        {
            "source_name": "Labor Contract Law",
            "source_section": "Article 35",
            "snippet": "The employer and employee may modify the labor contract by consensus.",
            "material_id": 1,
        }
    ]
    return {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "question": "Can my employer transfer me to another role?",
        "context_messages": [],
        "mock_chunks": chunks,
        "prompt_version": "prompt-backed:v1",
        "workflow_version": "legal_workflow:v1",
        "node_trace": [],
    }


def test_prompt_workflow_factory_assembles_full_prompt_backed_graph(tmp_path: Path) -> None:
    write_templates(tmp_path)
    factory = LegalPromptWorkflowFactory(
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(),
        llm_adapter=RoutingLLMAdapter(),
    )

    graph = factory.build_graph(workflow_prompts())
    result = cast(LegalWorkflowState, graph.invoke(initial_state()))

    assert result["category"] == "civil_labor"
    assert result["answer_draft"] == "Review the labor contract and negotiate first."
    assert result["validated_answer"] == "Review the labor contract and negotiate first."
    assert result["high_risk"] is False
    assert result["risk_reason"] is None
    assert result["error_code"] is None
    assert result["node_trace"] == [
        "input_safety",
        "classification",
        "context_build",
        "retrieval",
        "generation",
        "citation_check",
        "risk_check",
        "persist",
    ]
