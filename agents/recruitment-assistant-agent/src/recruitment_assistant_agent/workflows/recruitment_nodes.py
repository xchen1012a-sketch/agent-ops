"""Pure RECRUIT-240 workflow nodes with external services behind mock boundaries."""

from __future__ import annotations

from typing import cast

from recruitment_assistant_agent.rules.recruitment_mvp_rules import protected_attribute_fields
from recruitment_assistant_agent.workflows.recruitment_state import (
    GapHint,
    InterviewQuestionHint,
    JDRequirementHint,
    JDStructuredPayload,
    MatchItemHint,
    RecruitmentWorkflowState,
    RecruitmentWorkflowUpdate,
    ResumeStructuredPayload,
)

SUPPORTED_MATERIAL_KINDS = frozenset({"resume", "jd", "resume_jd"})
SENSITIVE_ATTRIBUTE_FIELDS = protected_attribute_fields()


def _trace(state: RecruitmentWorkflowState, node_name: str) -> list[str]:
    return [*state.get("node_trace", []), node_name]


def file_safety_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Validate material kind and expose the file-scan boundary."""

    if state["material_kind"] not in SUPPORTED_MATERIAL_KINDS:
        return {
            "file_safe": False,
            "scan_status": "blocked",
            "task_status": "failed",
            "persisted": False,
            "error_code": "UNSUPPORTED_MATERIAL_KIND",
            "boundary_message": (
                "暂不支持该材料类型，目前仅支持候选人简历、职位 JD，或简历+JD 组合。"
                "请上传对应材料后重试。"
            ),
            "node_trace": _trace(state, "file_safety"),
        }
    return {
        "file_safe": True,
        "scan_status": "clean",
        "error_code": None,
        "node_trace": _trace(state, "file_safety"),
    }


def task_route_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Move a safe task into the parsing phase."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "task_route")}
    if not state.get("file_safe", False):
        return {
            "task_status": "failed",
            "error_code": "FILE_UNSAFE",
            "node_trace": _trace(state, "task_route"),
        }
    return {"task_status": "parsing", "node_trace": _trace(state, "task_route")}


def resume_parse_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Consume adapter-provided resume structure without calling external services."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "resume_parse")}
    return {
        "resume_structure": state.get("mock_resume", _empty_resume_structure()),
        "node_trace": _trace(state, "resume_parse"),
    }


def jd_parse_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Consume adapter-provided JD structure without calling external services."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "jd_parse")}
    return {
        "jd_structure": state.get("mock_jd", _empty_jd_structure()),
        "task_status": "matching",
        "node_trace": _trace(state, "jd_parse"),
    }


def evidence_match_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Create deterministic match hints with explicit evidence/no-evidence separation."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "evidence_match")}

    requirements = state.get("jd_structure", {}).get("requirements", [])
    resume = state.get("resume_structure", {})
    match_items = [_match_requirement(requirement, resume) for requirement in requirements]
    overall_tier = _overall_tier(match_items)
    return {
        "match_items": match_items,
        "overall_tier": overall_tier,
        "node_trace": _trace(state, "evidence_match"),
    }


def fairness_check_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Enforce fairness by redacting protected attributes, then continuing.

    Discrimination risk is a safety boundary, but a candidate should not lose
    their whole evaluation because a parser happened to capture an ``age`` or
    ``gender`` field. Instead of failing the task, we strip every protected
    attribute from the parsed structures and continue on a fair,
    job-relevant-only payload — recording exactly what was removed so the
    redaction is auditable.
    """

    if state.get("error_code"):
        return {"node_trace": _trace(state, "fairness_check")}

    resume_structure = state.get("resume_structure", {})
    jd_structure = state.get("jd_structure", {})
    redacted_fields = sorted(
        _find_sensitive_fields(
            {"resume_structure": resume_structure, "jd_structure": jd_structure}
        )
    )
    if redacted_fields:
        return {
            "resume_structure": cast(
                "ResumeStructuredPayload", _redact_sensitive_fields(resume_structure)
            ),
            "jd_structure": cast(
                "JDStructuredPayload", _redact_sensitive_fields(jd_structure)
            ),
            "fairness_passed": True,
            "fairness_violation_details": redacted_fields,
            "boundary_message": _redaction_message(redacted_fields),
            "node_trace": _trace(state, "fairness_check"),
        }
    return {
        "fairness_passed": True,
        "fairness_violation_details": [],
        "node_trace": _trace(state, "fairness_check"),
    }


def _redaction_message(redacted_fields: list[str]) -> str:
    return (
        "检测到材料中包含受保护的敏感信息（"
        + "、".join(redacted_fields)
        + "），已自动脱敏后继续评估。本次分析仅依据与岗位相关的能力与经历，"
        "不会使用上述字段。"
    )


def gap_question_gen_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Generate deterministic gap descriptions and seed interview questions."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "gap_question_gen")}

    weak_items = [
        item
        for item in state.get("match_items", [])
        if item["match_status"] in {"partial", "no_evidence"}
    ]
    gaps = [_gap_from_match_item(item) for item in weak_items]
    questions = [_question_from_gap(gap) for gap in gaps]
    return {
        "gaps": gaps,
        "interview_questions": questions,
        "task_status": "ready_to_persist",
        "node_trace": _trace(state, "gap_question_gen"),
    }


def persist_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
    """Expose the persistence boundary without writing to the database yet."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "persist")}
    if state.get("simulate_db_unavailable", False):
        return {
            "persisted": False,
            "task_status": "failed",
            "error_code": "DB_UNAVAILABLE",
            "node_trace": _trace(state, "persist"),
        }
    return {
        "persisted": True,
        "task_status": "completed",
        "node_trace": _trace(state, "persist"),
    }


def _empty_resume_structure() -> ResumeStructuredPayload:
    return {"skills": [], "experiences": [], "educations": [], "soft_skills": []}


def _empty_jd_structure() -> JDStructuredPayload:
    return {"requirements": []}


def _match_requirement(
    requirement: JDRequirementHint,
    resume: ResumeStructuredPayload,
) -> MatchItemHint:
    requirement_text = requirement["text"]
    skill_evidence = _find_skill_evidence(requirement_text, resume)
    if skill_evidence is not None:
        return {
            "requirement": requirement_text,
            "match_status": "match",
            "evidence_snippet": skill_evidence,
            "skill_category": requirement.get("category"),
        }

    soft_skill_evidence = _find_soft_skill_evidence(requirement_text, resume)
    if soft_skill_evidence is not None:
        return {
            "requirement": requirement_text,
            "match_status": "partial",
            "evidence_snippet": soft_skill_evidence,
            "skill_category": requirement.get("category"),
        }

    return {
        "requirement": requirement_text,
        "match_status": "no_evidence",
        "skill_category": requirement.get("category"),
    }


def _find_skill_evidence(requirement_text: str, resume: ResumeStructuredPayload) -> str | None:
    lowered_requirement = requirement_text.lower()
    for skill in resume.get("skills", []):
        skill_name = skill["skill_name"].lower()
        if skill_name in lowered_requirement:
            return skill["evidence_snippet"]
    return None


def _find_soft_skill_evidence(requirement_text: str, resume: ResumeStructuredPayload) -> str | None:
    lowered_requirement = requirement_text.lower()
    for soft_skill in resume.get("soft_skills", []):
        if soft_skill.lower() in lowered_requirement:
            return soft_skill
    return None


def _overall_tier(match_items: list[MatchItemHint]) -> str | None:
    if not match_items:
        return None
    matched_count = sum(1 for item in match_items if item["match_status"] == "match")
    if matched_count == len(match_items):
        return "strong"
    if matched_count > 0:
        return "medium"
    return "weak"


def _find_sensitive_fields(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {key for key in value if key in SENSITIVE_ATTRIBUTE_FIELDS}
        for nested_value in value.values():
            found.update(_find_sensitive_fields(nested_value))
        return found
    if isinstance(value, list):
        list_found: set[str] = set()
        for item in value:
            list_found.update(_find_sensitive_fields(item))
        return list_found
    return set()


def _redact_sensitive_fields(value: object) -> object:
    """Return a deep copy with every protected-attribute key removed."""
    if isinstance(value, dict):
        return {
            key: _redact_sensitive_fields(nested)
            for key, nested in value.items()
            if key not in SENSITIVE_ATTRIBUTE_FIELDS
        }
    if isinstance(value, list):
        return [_redact_sensitive_fields(item) for item in value]
    return value


def _gap_from_match_item(item: MatchItemHint) -> GapHint:
    requirement = item["requirement"]
    if item["match_status"] == "no_evidence":
        return {
            "gap_description": f"未找到与要求“{requirement}”对应的候选人证据。",
            "suggested_question": f"请举例说明你如何满足“{requirement}”这项要求。",
        }
    return {
        "gap_description": f"要求“{requirement}”只有部分证据，需要进一步确认。",
        "suggested_question": f"请补充说明你在“{requirement}”方面的真实经验。",
    }


def _question_from_gap(gap: GapHint) -> InterviewQuestionHint:
    return {
        "question_text": gap["suggested_question"] or gap["gap_description"],
        "category": "gap_follow_up",
        "difficulty": "medium",
    }
