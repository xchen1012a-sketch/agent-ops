"""Unit tests for prompt-backed legal classification."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from legal_consulting_agent.application.services import (
    LegalClassificationPromptService,
    make_prompt_classification_node,
)
from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.domain.value_objects.legal_enums import PromptStatus
from legal_consulting_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from legal_consulting_agent.workflows import build_legal_workflow_graph
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState


class StaticLLMAdapter:
    """Test adapter that returns a fixed JSON string and records prompts."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def classification_prompt() -> PromptVersion:
    return PromptVersion(
        id=1,
        prompt_name="legal_classification",
        version="v1",
        template_key="legal_classification/v1/template.txt",
        variables={"required": ["question"]},
        output_schema={
            "type": "object",
            "required": ["category", "intent", "legal_entities"],
            "properties": {
                "category": {"type": "string"},
                "intent": {"type": "string"},
                "legal_entities": {"type": "object"},
            },
        },
        status=PromptStatus.ACTIVE,
        created_by=1,
    )


def write_template(root: Path) -> None:
    path = root / "legal_classification" / "v1" / "template.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("请对法律问题分类：{question}", encoding="utf-8")


def base_state() -> LegalWorkflowState:
    return {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "question": "公司单方面调岗，我可以拒绝吗？",
        "safe_question": "公司单方面调岗，我可以拒绝吗？",
        "is_safe": True,
        "prompt_version": "legal_classification:v1",
        "workflow_version": "legal_workflow:v1",
        "node_trace": ["input_safety"],
    }


def build_service(tmp_path: Path, response: str) -> LegalClassificationPromptService:
    write_template(tmp_path)
    return LegalClassificationPromptService(
        prompt=classification_prompt(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(),
        llm_adapter=StaticLLMAdapter(response),
    )


def test_classification_service_renders_prompt_and_validates_output(tmp_path: Path) -> None:
    adapter = StaticLLMAdapter(
        '{"category":"civil_labor","intent":"询问劳动调岗争议",'
        '"legal_entities":{"case_keywords":["调岗"]}}'
    )
    write_template(tmp_path)
    service = LegalClassificationPromptService(
        prompt=classification_prompt(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(),
        llm_adapter=adapter,
    )

    result = service.classify("公司单方面调岗，我可以拒绝吗？")

    assert "公司单方面调岗" in adapter.prompts[0]
    assert result.category == "civil_labor"
    assert result.intent == "询问劳动调岗争议"
    assert result.legal_entities == {
        "statute_numbers": [],
        "statute_names": [],
        "case_keywords": ["调岗"],
    }


def test_prompt_classification_node_updates_state(tmp_path: Path) -> None:
    service = build_service(
        tmp_path,
        '{"category":"civil_labor","intent":"询问劳动调岗争议","legal_entities":{}}',
    )
    node = make_prompt_classification_node(service)

    result = node(base_state())

    assert result["category"] == "civil_labor"
    assert result["intent"] == "询问劳动调岗争议"
    assert "error_code" not in result
    assert result["node_trace"] == ["input_safety", "classification"]


def test_prompt_classification_node_degrades_invalid_output_to_general(
    tmp_path: Path,
) -> None:
    service = build_service(tmp_path, '{"category": ["bad"], "intent": "x", "legal_entities": {}}')
    node = make_prompt_classification_node(service)

    result = node(base_state())

    # Fail-open: malformed classification degrades to a general legal question
    # that still gets answered, instead of a hard CLASSIFY_FAILED refusal.
    assert result["category"] == "general"
    assert "error_code" not in result


def test_graph_accepts_prompt_backed_classification_node(tmp_path: Path) -> None:
    service = build_service(
        tmp_path,
        '{"category":"civil_labor","intent":"询问劳动调岗争议","legal_entities":{}}',
    )
    node = make_prompt_classification_node(service)
    graph = build_legal_workflow_graph(classification_handler=node)

    result = cast(LegalWorkflowState, graph.invoke(base_state()))

    assert result["category"] == "civil_labor"
    assert result["intent"] == "询问劳动调岗争议"
    assert result["error_code"] is None
