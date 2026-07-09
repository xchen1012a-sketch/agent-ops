"""Unit tests for prompt-backed legal risk check."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from legal_consulting_agent.application.services import (
    LegalRiskCheckPromptService,
    make_prompt_risk_check_node,
)
from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.domain.value_objects.legal_enums import PromptStatus
from legal_consulting_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from legal_consulting_agent.workflows import build_legal_workflow_graph
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState, LegalWorkflowUpdate
from tests.unit.test_classification_prompt_service import StaticLLMAdapter


def risk_check_prompt() -> PromptVersion:
    return PromptVersion(
        id=3,
        prompt_name="legal_risk_check",
        version="v1",
        template_key="legal_risk_check/v1/template.txt",
        variables={"required": ["question", "answer", "citations", "category"]},
        output_schema={
            "type": "object",
            "required": ["high_risk", "risk_reason"],
            "properties": {
                "high_risk": {"type": "boolean"},
                "risk_reason": {"type": ["string", "null"]},
            },
        },
        status=PromptStatus.ACTIVE,
        created_by=1,
    )


def write_template(root: Path) -> None:
    path = root / "legal_risk_check" / "v1" / "template.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Question: {question}\nCategory: {category}\nAnswer: {answer}\nCitations: {citations}",
        encoding="utf-8",
    )


def build_service(tmp_path: Path, response: str) -> LegalRiskCheckPromptService:
    write_template(tmp_path)
    return LegalRiskCheckPromptService(
        prompt=risk_check_prompt(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(),
        llm_adapter=StaticLLMAdapter(response),
    )


def base_state() -> LegalWorkflowState:
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
        "safe_question": "Can my employer transfer me to another role?",
        "is_safe": True,
        "category": "civil_labor",
        "intent": "labor contract dispute",
        "context_messages": [],
        "chunks": chunks,
        "mock_chunks": chunks,
        "answer_draft": "Review the contract and negotiate first.",
        "validated_answer": "Review the contract and negotiate first.",
        "citations": [
            {
                "source": "Labor Contract Law",
                "section": "Article 35",
                "snippet": "The employer and employee may modify the labor contract by consensus.",
            }
        ],
        "prompt_version": "legal_risk_check:v1",
        "workflow_version": "legal_workflow:v1",
        "node_trace": [
            "input_safety",
            "classification",
            "context_build",
            "retrieval",
            "generation",
            "citation_check",
        ],
    }


def test_risk_check_service_accepts_high_risk_reason(tmp_path: Path) -> None:
    service = build_service(tmp_path, '{"high_risk":true,"risk_reason":"personal_safety"}')

    result = service.assess(
        question="Question involving immediate safety risk",
        answer="Seek emergency help and preserve evidence.",
        citations=[],
        category="family",
    )

    assert result.high_risk is True
    assert result.risk_reason == "personal_safety"


def test_risk_check_service_accepts_null_low_risk_reason(tmp_path: Path) -> None:
    service = build_service(tmp_path, '{"high_risk":false,"risk_reason":null}')

    result = service.assess(
        question="Can my employer transfer me?",
        answer="Review the contract and negotiate first.",
        citations=[],
        category="civil_labor",
    )

    assert result.high_risk is False
    assert result.risk_reason is None


def test_prompt_risk_check_node_fails_closed_on_invalid_output(tmp_path: Path) -> None:
    service = build_service(tmp_path, '{"high_risk":true,"risk_reason":null}')
    node = make_prompt_risk_check_node(service)

    result = node(base_state())

    assert result["high_risk"] is True
    assert result["risk_reason"] == "risk_check_validation_failed"
    assert "error_code" not in result


def test_graph_accepts_prompt_backed_risk_check_node(tmp_path: Path) -> None:
    service = build_service(tmp_path, '{"high_risk":false,"risk_reason":null}')
    risk_node = make_prompt_risk_check_node(service)

    def classification_handler(state: LegalWorkflowState) -> LegalWorkflowUpdate:
        return {
            "category": "civil_labor",
            "intent": "labor contract dispute",
            "legal_entities": {},
            "node_trace": [*state.get("node_trace", []), "classification"],
        }

    def generation_handler(state: LegalWorkflowState) -> LegalWorkflowUpdate:
        return {
            "answer_draft": "Review the contract and negotiate first.",
            "citations": [
                {
                    "source": "Labor Contract Law",
                    "section": "Article 35",
                    "snippet": "The employer and employee may modify the labor contract by consensus.",
                }
            ],
            "node_trace": [*state.get("node_trace", []), "generation"],
        }

    graph = build_legal_workflow_graph(
        classification_handler=classification_handler,
        generation_handler=generation_handler,
        risk_check_handler=risk_node,
    )
    state = base_state()
    state["node_trace"] = []

    result = cast(LegalWorkflowState, graph.invoke(state))

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
