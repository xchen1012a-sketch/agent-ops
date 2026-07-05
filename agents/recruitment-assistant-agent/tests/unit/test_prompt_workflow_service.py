"""Unit tests for prompt-backed recruitment workflow nodes."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import cast

from recruitment_assistant_agent.application.services.prompt_workflow_service import (
    EvidenceMatchPromptService,
    FairnessCheckPromptService,
    GapQuestionPromptService,
    JDParsePromptService,
    make_prompt_evidence_match_node,
    make_prompt_fairness_check_node,
    make_prompt_gap_question_node,
    make_prompt_jd_parse_node,
)
from recruitment_assistant_agent.domain.entities.recruit_data import PromptVersion
from recruitment_assistant_agent.domain.value_objects.recruit_enums import PromptStatus
from recruitment_assistant_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from recruitment_assistant_agent.workflows.recruitment_graph import build_recruitment_workflow_graph
from recruitment_assistant_agent.workflows.recruitment_state import (
    RecruitmentWorkflowState,
)


class SequenceLLMAdapter:
    def __init__(self, raw_outputs: Sequence[str]) -> None:
        self._raw_outputs = list(raw_outputs)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._raw_outputs.pop(0)


class FailingLLMAdapter:
    def complete(self, prompt: str) -> str:
        raise TimeoutError("provider timeout with raw prompt")


def prompt_version(
    *,
    prompt_name: str,
    template_key: str,
    required_variables: list[str],
    output_schema: dict[str, object],
) -> PromptVersion:
    return PromptVersion(
        public_id=f"{prompt_name}-public-id",
        prompt_name=prompt_name,
        version="v1",
        template_key=template_key,
        status=PromptStatus.ACTIVE,
        created_by=1,
        variables={"required": required_variables},
        output_schema=output_schema,
    )


def write_templates(root: Path) -> None:
    templates = {
        "recruit_jd_parse/v1/template.txt": "JD: {jd_text}",
        "recruit_evidence_match/v1/template.txt": "Resume: {resume_structure}\nJD: {jd_structure}",
        "recruit_fairness_check/v1/template.txt": "Check: {resume_structure} {jd_structure} {match_items}",
        "recruit_gap_question/v1/template.txt": "Gaps: {match_items}",
    }
    for key, content in templates.items():
        path = root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def jd_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["job_title", "summary", "requirements"],
        "properties": {
            "job_title": {"type": "string"},
            "summary": {"type": "string"},
            "requirements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["requirement_type", "text"],
                    "properties": {
                        "requirement_type": {"type": "string"},
                        "text": {"type": "string"},
                        "category": {"type": "string"},
                        "weight_hint": {"type": "number"},
                    },
                },
            },
        },
    }


def evidence_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["match_items", "overall_tier"],
        "properties": {
            "match_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["requirement", "match_status"],
                    "properties": {
                        "requirement": {"type": "string"},
                        "match_status": {"type": "string"},
                        "evidence_snippet": {"type": "string"},
                        "skill_category": {"type": "string"},
                    },
                },
            },
            "overall_tier": {"type": "string"},
        },
    }


def fairness_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["fairness_passed", "violation_details"],
        "properties": {
            "fairness_passed": {"type": "boolean"},
            "violation_details": {"type": "array", "items": {"type": "string"}},
        },
    }


def gap_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["gaps", "interview_questions"],
        "properties": {
            "gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["gap_description"],
                    "properties": {
                        "gap_description": {"type": "string"},
                        "suggested_question": {"type": "string"},
                    },
                },
            },
            "interview_questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["question_text", "category"],
                    "properties": {
                        "question_text": {"type": "string"},
                        "category": {"type": "string"},
                        "difficulty": {"type": "string"},
                    },
                },
            },
        },
    }


def jd_raw_output() -> str:
    return """
    {
      "job_title": "Backend Engineer",
      "summary": "Build Python services.",
      "requirements": [
        {"requirement_type": "must_have", "text": "Python", "category": "backend", "weight_hint": 0.8},
        {"requirement_type": "nice_to_have", "text": "Kubernetes", "category": "platform", "weight_hint": 0.2}
      ]
    }
    """


def evidence_raw_output() -> str:
    return """
    {
      "match_items": [
        {"requirement": "Python", "match_status": "match", "evidence_snippet": "Built Python APIs.", "skill_category": "backend"},
        {"requirement": "Kubernetes", "match_status": "no_evidence", "skill_category": "platform"}
      ],
      "overall_tier": "medium"
    }
    """


def fairness_pass_raw_output() -> str:
    return """
    {"fairness_passed": true, "violation_details": []}
    """


def fairness_fail_raw_output() -> str:
    return """
    {"fairness_passed": false, "violation_details": ["contains gender evidence"]}
    """


def gap_raw_output() -> str:
    return """
    {
      "gaps": [{"gap_description": "No Kubernetes evidence.", "suggested_question": "Tell us about Kubernetes operations."}],
      "interview_questions": [{"question_text": "How have you operated Kubernetes in production-like environments?", "category": "technical", "difficulty": "medium"}]
    }
    """


def base_state() -> RecruitmentWorkflowState:
    return {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruit_prompt:v1",
        "workflow_version": "recruitment_workflow:v1",
        "mock_resume_text": "Built Python APIs.",
        "mock_jd_text": "Need Python and Kubernetes.",
        "simulate_db_unavailable": False,
    }


def service_bundle(
    tmp_path: Path, adapter: SequenceLLMAdapter | FailingLLMAdapter
) -> tuple[
    JDParsePromptService,
    EvidenceMatchPromptService,
    FairnessCheckPromptService,
    GapQuestionPromptService,
]:
    write_templates(tmp_path)
    loader = PromptTemplateLoader(tmp_path)
    return (
        JDParsePromptService(
            prompt=prompt_version(
                prompt_name="recruit_jd_parse",
                template_key="recruit_jd_parse/v1/template.txt",
                required_variables=["jd_text"],
                output_schema=jd_schema(),
            ),
            template_loader=loader,
            output_validator=PromptOutputValidator(jd_schema()),
            llm_adapter=adapter,
        ),
        EvidenceMatchPromptService(
            prompt=prompt_version(
                prompt_name="recruit_evidence_match",
                template_key="recruit_evidence_match/v1/template.txt",
                required_variables=["resume_structure", "jd_structure"],
                output_schema=evidence_schema(),
            ),
            template_loader=loader,
            output_validator=PromptOutputValidator(evidence_schema()),
            llm_adapter=adapter,
        ),
        FairnessCheckPromptService(
            prompt=prompt_version(
                prompt_name="recruit_fairness_check",
                template_key="recruit_fairness_check/v1/template.txt",
                required_variables=["resume_structure", "jd_structure", "match_items"],
                output_schema=fairness_schema(),
            ),
            template_loader=loader,
            output_validator=PromptOutputValidator(fairness_schema()),
            llm_adapter=adapter,
        ),
        GapQuestionPromptService(
            prompt=prompt_version(
                prompt_name="recruit_gap_question",
                template_key="recruit_gap_question/v1/template.txt",
                required_variables=["match_items"],
                output_schema=gap_schema(),
            ),
            template_loader=loader,
            output_validator=PromptOutputValidator(gap_schema()),
            llm_adapter=adapter,
        ),
    )


def test_prompt_services_shape_outputs(tmp_path: Path) -> None:
    jd_service, evidence_service, fairness_service, gap_service = service_bundle(
        tmp_path,
        SequenceLLMAdapter(
            [jd_raw_output(), evidence_raw_output(), fairness_pass_raw_output(), gap_raw_output()]
        ),
    )

    jd_result = jd_service.parse("Need Python and Kubernetes.")
    evidence_result = evidence_service.match(
        resume_structure={"skills": [{"skill_name": "Python"}]},
        jd_structure=jd_result.jd_structure,
    )
    fairness_result = fairness_service.check(
        resume_structure={"skills": [{"skill_name": "Python"}]},
        jd_structure=jd_result.jd_structure,
        match_items=evidence_result.match_items,
    )
    gap_result = gap_service.generate(match_items=evidence_result.match_items)

    assert jd_result.jd_structure["job_title"] == "Backend Engineer"
    assert jd_result.jd_structure["requirements"][0]["weight_hint"] == 0.8
    assert evidence_result.overall_tier == "medium"
    assert evidence_result.match_items[1]["match_status"] == "no_evidence"
    assert "evidence_snippet" not in evidence_result.match_items[1]
    assert fairness_result.fairness_passed is True
    assert fairness_result.violation_details == []
    assert gap_result.gaps[0]["gap_description"] == "No Kubernetes evidence."
    assert gap_result.interview_questions[0]["category"] == "technical"


def test_prompt_nodes_return_expected_updates(tmp_path: Path) -> None:
    jd_service, evidence_service, fairness_service, gap_service = service_bundle(
        tmp_path,
        SequenceLLMAdapter(
            [jd_raw_output(), evidence_raw_output(), fairness_pass_raw_output(), gap_raw_output()]
        ),
    )
    state = base_state()

    jd_update = make_prompt_jd_parse_node(jd_service)(state)
    state = cast(RecruitmentWorkflowState, {**state, **jd_update})
    evidence_update = make_prompt_evidence_match_node(evidence_service)(state)
    state = cast(RecruitmentWorkflowState, {**state, **evidence_update})
    fairness_update = make_prompt_fairness_check_node(fairness_service)(state)
    state = cast(RecruitmentWorkflowState, {**state, **fairness_update})
    gap_update = make_prompt_gap_question_node(gap_service)(state)

    assert jd_update["task_status"] == "matching"
    assert evidence_update["overall_tier"] == "medium"
    assert fairness_update["fairness_passed"] is True
    assert gap_update["task_status"] == "ready_to_persist"
    assert gap_update["interview_questions"][0]["difficulty"] == "medium"


def test_prompt_fairness_node_blocks_failed_check(tmp_path: Path) -> None:
    _, _, fairness_service, _ = service_bundle(
        tmp_path,
        SequenceLLMAdapter([fairness_fail_raw_output()]),
    )
    state = base_state()
    state["resume_structure"] = {"skills": []}
    state["jd_structure"] = {"requirements": []}
    state["match_items"] = []

    update = make_prompt_fairness_check_node(fairness_service)(state)

    assert update["fairness_passed"] is False
    assert update["task_status"] == "failed"
    assert update["persisted"] is False
    assert update["error_code"] == "FAIRNESS_VIOLATION"
    assert update["fairness_violation_details"] == ["contains gender evidence"]


def test_prompt_node_converts_adapter_error_to_failed_update(tmp_path: Path) -> None:
    jd_service, _, _, _ = service_bundle(tmp_path, FailingLLMAdapter())

    update = make_prompt_jd_parse_node(jd_service)(base_state())

    assert update["error_code"] == "PARSE_FAILED"
    assert update["task_status"] == "failed"
    assert update["persisted"] is False
    assert update["node_trace"] == ["jd_parse"]


def test_prompt_fairness_node_converts_adapter_error_to_parse_failed(tmp_path: Path) -> None:
    _, _, fairness_service, _ = service_bundle(tmp_path, FailingLLMAdapter())
    state = base_state()
    state["resume_structure"] = {"skills": []}
    state["jd_structure"] = {"requirements": []}
    state["match_items"] = []

    update = make_prompt_fairness_check_node(fairness_service)(state)

    assert update["error_code"] == "PARSE_FAILED"
    assert update["task_status"] == "failed"
    assert update["persisted"] is False
    assert update["node_trace"] == ["fairness_check"]


def test_prompt_fairness_node_fails_closed_on_sensitive_fields(tmp_path: Path) -> None:
    _, _, fairness_service, _ = service_bundle(
        tmp_path,
        SequenceLLMAdapter([fairness_pass_raw_output()]),
    )
    state = base_state()
    state["resume_structure"] = {"skills": [], "gender": "redacted"}
    state["jd_structure"] = {"requirements": []}
    state["match_items"] = []

    update = make_prompt_fairness_check_node(fairness_service)(state)

    assert update["fairness_passed"] is False
    assert update["error_code"] == "FAIRNESS_VIOLATION"
    assert update["fairness_violation_details"] == ["gender"]
    assert update["node_trace"] == ["fairness_check"]


def test_graph_runs_prompt_backed_matching_nodes(tmp_path: Path) -> None:
    jd_service, evidence_service, fairness_service, gap_service = service_bundle(
        tmp_path,
        SequenceLLMAdapter(
            [jd_raw_output(), evidence_raw_output(), fairness_pass_raw_output(), gap_raw_output()]
        ),
    )
    graph = build_recruitment_workflow_graph(
        jd_parse_handler=make_prompt_jd_parse_node(jd_service),
        evidence_match_handler=make_prompt_evidence_match_node(evidence_service),
        fairness_check_handler=make_prompt_fairness_check_node(fairness_service),
        gap_question_gen_handler=make_prompt_gap_question_node(gap_service),
    )

    result = cast(RecruitmentWorkflowState, graph.invoke(base_state()))

    assert result["error_code"] is None
    assert result["task_status"] == "completed"
    assert result["persisted"] is True
    assert result["overall_tier"] == "medium"
    assert result["gaps"][0]["suggested_question"] == "Tell us about Kubernetes operations."
    assert result["node_trace"] == [
        "file_safety",
        "task_route",
        "resume_parse",
        "jd_parse",
        "evidence_match",
        "fairness_check",
        "gap_question_gen",
        "persist",
    ]
