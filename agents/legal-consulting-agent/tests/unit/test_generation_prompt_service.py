"""Unit tests for prompt-backed legal answer generation."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from legal_consulting_agent.application.services import (
    LegalGenerationPromptService,
    make_prompt_generation_node,
)
from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.domain.value_objects.legal_enums import PromptStatus
from legal_consulting_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from legal_consulting_agent.workflows import build_legal_workflow_graph
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState
from tests.unit.test_classification_prompt_service import StaticLLMAdapter


def generation_prompt() -> PromptVersion:
    return PromptVersion(
        id=2,
        prompt_name="legal_generation",
        version="v1",
        template_key="legal_generation/v1/template.txt",
        variables={"required": ["question", "context", "chunks", "category"]},
        output_schema={
            "type": "object",
            "required": ["answer", "citations"],
            "properties": {
                "answer": {"type": "string"},
                "citations": {"type": "array"},
            },
        },
        status=PromptStatus.ACTIVE,
        created_by=1,
    )


def write_template(root: Path) -> None:
    path = root / "legal_generation" / "v1" / "template.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "问题：{question}\n分类：{category}\n上下文：{context}\n片段：{chunks}",
        encoding="utf-8",
    )


def base_state() -> LegalWorkflowState:
    chunks = [
        {
            "source_name": "中华人民共和国劳动合同法",
            "source_section": "第三十五条",
            "snippet": "用人单位与劳动者协商一致，可以变更劳动合同约定的内容。",
            "material_id": 1,
        }
    ]
    return {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "question": "公司单方面调岗，我可以拒绝吗？",
        "safe_question": "公司单方面调岗，我可以拒绝吗？",
        "is_safe": True,
        "category": "civil_labor",
        "intent": "询问劳动调岗争议",
        "context_messages": [],
        "chunks": chunks,
        "mock_chunks": chunks,
        "prompt_version": "legal_generation:v1",
        "workflow_version": "legal_workflow:v1",
        "node_trace": ["input_safety", "classification", "context_build", "retrieval"],
    }


def build_service(tmp_path: Path, response: str) -> LegalGenerationPromptService:
    write_template(tmp_path)
    return LegalGenerationPromptService(
        prompt=generation_prompt(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(),
        llm_adapter=StaticLLMAdapter(response),
    )


def valid_generation_response() -> str:
    return (
        '{"answer":"需要结合劳动合同约定和协商情况判断。",'
        '"citations":[{"source":"中华人民共和国劳动合同法","section":"第三十五条",'
        '"snippet":"用人单位与劳动者协商一致，可以变更劳动合同约定的内容。"}]}'
    )


def test_generation_service_renders_prompt_and_validates_output(tmp_path: Path) -> None:
    service = build_service(tmp_path, valid_generation_response())

    result = service.generate(
        question="公司单方面调岗，我可以拒绝吗？",
        context_messages=[],
        chunks=base_state()["chunks"],
        category="civil_labor",
    )

    assert result.answer == "需要结合劳动合同约定和协商情况判断。"
    assert result.citations == [
        {
            "source": "中华人民共和国劳动合同法",
            "section": "第三十五条",
            "snippet": "用人单位与劳动者协商一致，可以变更劳动合同约定的内容。",
        }
    ]


def test_prompt_generation_node_updates_answer_and_citations(tmp_path: Path) -> None:
    service = build_service(tmp_path, valid_generation_response())
    node = make_prompt_generation_node(service)

    result = node(base_state())

    assert result["answer_draft"] == "需要结合劳动合同约定和协商情况判断。"
    assert result["citations"] == [
        {
            "source": "中华人民共和国劳动合同法",
            "section": "第三十五条",
            "snippet": "用人单位与劳动者协商一致，可以变更劳动合同约定的内容。",
        }
    ]
    assert result["node_trace"] == [
        "input_safety",
        "classification",
        "context_build",
        "retrieval",
        "generation",
    ]


def test_prompt_generation_node_maps_invalid_output_to_citation_invalid(
    tmp_path: Path,
) -> None:
    service = build_service(tmp_path, '{"answer":"缺少引用","citations":{}}')
    node = make_prompt_generation_node(service)

    result = node(base_state())

    assert result["answer_draft"] is None
    assert result["citations"] == []
    assert result["error_code"] == "CITATION_INVALID"


class RecordingLLMAdapter:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def test_generation_prompt_prepends_system_policy(tmp_path: Path) -> None:
    write_template(tmp_path)
    adapter = RecordingLLMAdapter(valid_generation_response())
    service = LegalGenerationPromptService(
        prompt=generation_prompt(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(),
        llm_adapter=adapter,
    )

    service.generate(
        question="公司单方面调岗，我可以拒绝吗？",
        context_messages=[],
        chunks=base_state()["chunks"],
        category="civil_labor",
    )

    assert adapter.last_prompt is not None
    # Identity + refusal policy reaches the model, ahead of the task prompt.
    assert "你是「法律咨询助手」" in adapter.last_prompt
    assert "拒绝规则" in adapter.last_prompt
    assert "公司单方面调岗" in adapter.last_prompt


def test_graph_accepts_prompt_backed_generation_node(tmp_path: Path) -> None:
    service = build_service(tmp_path, valid_generation_response())
    node = make_prompt_generation_node(service)
    graph = build_legal_workflow_graph(generation_handler=node)

    result = cast(LegalWorkflowState, graph.invoke(base_state()))

    assert result["answer_draft"] == "需要结合劳动合同约定和协商情况判断。"
    assert result["error_code"] is None
