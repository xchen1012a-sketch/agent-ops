"""State schema for the recruitment analysis workflow.

This module intentionally contains only typed state contracts. Nodes and
adapters must depend on this schema rather than passing unstructured dicts.
"""

from __future__ import annotations

from typing import Required, TypedDict


class SkillEvidenceHint(TypedDict, total=False):
    """A skill evidence row produced by resume parsing."""

    skill_name: Required[str]
    evidence_snippet: Required[str]
    source_section: str | None
    proficiency: str | None


class ExperienceEvidenceHint(TypedDict, total=False):
    """A work experience evidence row produced by resume parsing."""

    role_title: Required[str]
    evidence_snippet: Required[str]
    company_redacted: str | None
    duration_months: int | None


class EducationEvidenceHint(TypedDict, total=False):
    """An education evidence row produced by resume parsing."""

    evidence_snippet: Required[str]
    degree: str | None
    major: str | None
    school_tier: str | None
    graduation_year: int | None


class ResumeStructuredPayload(TypedDict, total=False):
    """Structured resume payload persisted after parsing.

    Sensitive attributes (age, gender, marital status, ethnicity, health,
    political status, photo, id card, hometown, religion, hukou) must NEVER
    appear in this payload; ``fairness_check_node`` will fail-closed if any
    of those field names are detected.
    """

    summary: str | None
    total_years_exp: float | None
    skills: list[SkillEvidenceHint]
    experiences: list[ExperienceEvidenceHint]
    educations: list[EducationEvidenceHint]
    soft_skills: list[str]


class JDRequirementHint(TypedDict, total=False):
    """A JD requirement row produced by JD parsing."""

    requirement_type: Required[str]
    text: Required[str]
    category: str | None
    weight_hint: float | None


class JDStructuredPayload(TypedDict, total=False):
    """Structured JD payload persisted after parsing."""

    job_title: str | None
    summary: str | None
    requirements: list[JDRequirementHint]


class MatchItemHint(TypedDict, total=False):
    """A per-requirement match item produced by evidence matching."""

    requirement: Required[str]
    match_status: Required[str]
    evidence_snippet: str | None
    skill_category: str | None


class GapHint(TypedDict, total=False):
    """A gap description with an optional seed interview question."""

    gap_description: Required[str]
    suggested_question: str | None


class InterviewQuestionHint(TypedDict, total=False):
    """A structured interview question produced by gap_question_gen."""

    question_text: Required[str]
    category: Required[str]
    difficulty: str | None


class RecruitmentWorkflowState(TypedDict, total=False):
    """LangGraph state for RECRUIT-240.

    The first workflow slice keeps external services behind mock boundaries:
    no DeepSeek, ClamAV, file storage, or database side effects are triggered
    by these fields alone. Test callers may inject ``mock_resume`` /
    ``mock_jd`` to drive deterministic parsing paths.
    """

    thread_id: Required[str]
    user_id: Required[int]
    task_id: Required[int]
    material_kind: Required[str]
    prompt_version: Required[str]
    workflow_version: Required[str]

    file_safe: bool
    scan_status: str | None
    task_status: str | None
    resume_structure: ResumeStructuredPayload
    jd_structure: JDStructuredPayload
    match_items: list[MatchItemHint]
    overall_tier: str | None
    fairness_passed: bool
    fairness_violation_details: list[str]
    gaps: list[GapHint]
    interview_questions: list[InterviewQuestionHint]
    persisted: bool
    error_code: str | None
    node_trace: list[str]

    # Test-only / adapter boundary inputs. Production callers should provide
    # these through explicit adapters in later slices, not from HTTP payloads.
    mock_resume: ResumeStructuredPayload
    mock_jd: JDStructuredPayload
    simulate_db_unavailable: bool


class RecruitmentWorkflowUpdate(TypedDict, total=False):
    """Partial state update returned by a workflow node."""

    file_safe: bool
    scan_status: str | None
    task_status: str | None
    resume_structure: ResumeStructuredPayload
    jd_structure: JDStructuredPayload
    match_items: list[MatchItemHint]
    overall_tier: str | None
    fairness_passed: bool
    fairness_violation_details: list[str]
    gaps: list[GapHint]
    interview_questions: list[InterviewQuestionHint]
    persisted: bool
    error_code: str | None
    node_trace: list[str]
