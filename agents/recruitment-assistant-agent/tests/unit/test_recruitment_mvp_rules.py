"""Unit tests for versioned recruitment MVP rules."""

from __future__ import annotations

from recruitment_assistant_agent.rules import (
    load_recruitment_mvp_rules,
    protected_attribute_fields,
    rule_version,
    skill_keywords,
    workflow_node_names,
)


def test_recruitment_mvp_rules_define_required_boundaries() -> None:
    rules = load_recruitment_mvp_rules()

    assert rule_version() == "recruitment_mvp:v1"
    assert "当前 docs/homework 只展开实训报告大纲" in str(rules["source_status"])
    assert "gender" in protected_attribute_fields()
    assert "python" in skill_keywords()
    assert workflow_node_names() == (
        "start",
        "file_safety",
        "resume_parse",
        "jd_parse",
        "evidence_match",
        "fairness_check",
        "gap_question_gen",
        "report_template",
        "end",
    )
