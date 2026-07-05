"""Unit tests for the first RECRUIT-240 workflow slice."""

from __future__ import annotations

from typing import cast

import pytest

from recruitment_assistant_agent.workflows import build_recruitment_workflow_graph
from recruitment_assistant_agent.workflows.recruitment_nodes import (
    evidence_match_node,
    fairness_check_node,
    file_safety_node,
)
from recruitment_assistant_agent.workflows.recruitment_state import RecruitmentWorkflowState


def base_state() -> RecruitmentWorkflowState:
    return {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruitment_workflow:v1",
        "workflow_version": "recruitment_workflow:v1",
    }


def state_with_mock_inputs() -> RecruitmentWorkflowState:
    state = base_state()
    state["mock_resume"] = {
        "summary": "Python backend engineer.",
        "total_years_exp": 5.0,
        "skills": [
            {
                "skill_name": "Python",
                "evidence_snippet": "Built Python services for recruitment analytics.",
                "source_section": "skills",
                "proficiency": "advanced",
            }
        ],
        "experiences": [],
        "educations": [],
        "soft_skills": ["communication"],
    }
    state["mock_jd"] = {
        "job_title": "Backend Engineer",
        "summary": "Build hiring workflow services.",
        "requirements": [
            {
                "requirement_type": "must_have",
                "text": "Python service development",
                "category": "backend",
                "weight_hint": 0.7,
            },
            {
                "requirement_type": "nice_to_have",
                "text": "Stakeholder communication",
                "category": "soft_skill",
                "weight_hint": 0.3,
            },
            {
                "requirement_type": "must_have",
                "text": "Kubernetes operations",
                "category": "platform",
                "weight_hint": 0.5,
            },
        ],
    }
    return state


def test_file_safety_rejects_unsupported_material_kind() -> None:
    state = base_state()
    state["material_kind"] = "cover_letter"

    result = file_safety_node(state)

    assert result["file_safe"] is False
    assert result["scan_status"] == "blocked"
    assert result["error_code"] == "UNSUPPORTED_MATERIAL_KIND"
    assert result["node_trace"] == ["file_safety"]


def test_evidence_match_keeps_no_evidence_without_snippet() -> None:
    state = state_with_mock_inputs()
    state["resume_structure"] = state["mock_resume"]
    state["jd_structure"] = state["mock_jd"]

    result = evidence_match_node(state)

    statuses = [item["match_status"] for item in result["match_items"]]
    assert statuses == ["match", "partial", "no_evidence"]
    assert "evidence_snippet" not in result["match_items"][2]
    assert result["overall_tier"] == "medium"


@pytest.mark.parametrize(
    "field_name",
    [
        "age",
        "gender",
        "marital_status",
        "ethnicity",
        "health",
        "political_status",
        "photo",
        "id_card",
        "hometown",
        "religion",
        "hukou",
    ],
)
def test_fairness_check_fails_closed_on_each_sensitive_attribute(field_name: str) -> None:
    state = base_state()
    state["resume_structure"] = {
        "summary": "Candidate includes forbidden field.",
        "skills": [],
        "experiences": [
            {
                "role_title": "Engineer",
                "evidence_snippet": "Built services.",
                field_name: "redacted",
            }
        ],
        "educations": [],
        "soft_skills": [],
    }
    state["jd_structure"] = {"requirements": []}

    result = fairness_check_node(state)

    assert result["fairness_passed"] is False
    assert result["fairness_violation_details"] == [field_name]
    assert result["task_status"] == "failed"
    assert result["error_code"] == "FAIRNESS_VIOLATION"


def test_fairness_check_fails_closed_on_sensitive_attribute_field() -> None:
    state = base_state()
    state["resume_structure"] = {
        "summary": "Candidate includes forbidden field.",
        "skills": [],
        "experiences": [],
        "educations": [],
        "soft_skills": [],
        "gender": "redacted",
    }
    state["jd_structure"] = {"requirements": []}

    result = fairness_check_node(state)

    assert result["fairness_passed"] is False
    assert result["fairness_violation_details"] == ["gender"]
    assert result["error_code"] == "FAIRNESS_VIOLATION"


def test_graph_runs_mock_boundary_without_external_services() -> None:
    graph = build_recruitment_workflow_graph()

    result = cast(RecruitmentWorkflowState, graph.invoke(state_with_mock_inputs()))

    assert result["error_code"] is None
    assert result["file_safe"] is True
    assert result["scan_status"] == "clean"
    assert result["overall_tier"] == "medium"
    assert result["fairness_passed"] is True
    assert result["persisted"] is True
    assert result["task_status"] == "completed"
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
    assert len(result["gaps"]) == 2
    assert len(result["interview_questions"]) == 2


def test_graph_stops_after_file_safety_failure() -> None:
    graph = build_recruitment_workflow_graph()
    state = base_state()
    state["material_kind"] = "cover_letter"

    result = cast(RecruitmentWorkflowState, graph.invoke(state))

    assert result["file_safe"] is False
    assert result["task_status"] == "failed"
    assert result["error_code"] == "UNSUPPORTED_MATERIAL_KIND"
    assert result["node_trace"] == ["file_safety"]


def test_graph_stops_after_fairness_violation_without_persisting() -> None:
    graph = build_recruitment_workflow_graph()
    state = state_with_mock_inputs()
    state["mock_resume"]["id_card"] = "redacted"

    result = cast(RecruitmentWorkflowState, graph.invoke(state))

    assert result["fairness_passed"] is False
    assert result["task_status"] == "failed"
    assert result["persisted"] is False
    assert result["error_code"] == "FAIRNESS_VIOLATION"
    assert result["node_trace"] == [
        "file_safety",
        "task_route",
        "resume_parse",
        "jd_parse",
        "evidence_match",
        "fairness_check",
    ]


def test_graph_reports_db_unavailable_at_persist_boundary() -> None:
    graph = build_recruitment_workflow_graph()
    state = state_with_mock_inputs()
    state["simulate_db_unavailable"] = True

    result = cast(RecruitmentWorkflowState, graph.invoke(state))

    assert result["persisted"] is False
    assert result["task_status"] == "failed"
    assert result["error_code"] == "DB_UNAVAILABLE"
    assert result["node_trace"][-1] == "persist"
