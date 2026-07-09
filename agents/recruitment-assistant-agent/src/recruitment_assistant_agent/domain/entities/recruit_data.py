"""Domain entities for the RECRUIT-230 identity and data layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from recruitment_assistant_agent.domain.value_objects.recruit_enums import (
    Degree,
    MatchTier,
    MaterialKind,
    Proficiency,
    PromptStatus,
    QuestionCategory,
    QuestionDifficulty,
    RequirementType,
    ReviewStatus,
    RunStatus,
    ScanStatus,
    SchoolTier,
    SkillCategory,
    TaskPriority,
    TaskStatus,
    UserRole,
    UserStatus,
)


@dataclass(frozen=True, slots=True)
class UserMirror:
    """Unified-auth user mirror stored by the recruitment Agent.

    Passwords and refresh tokens remain outside this service.
    """

    public_id: str
    email: str
    display_name: str | None
    role: UserRole
    status: UserStatus
    id: int | None = None


@dataclass(frozen=True, slots=True)
class RecruitTask:
    """Recruitment analysis task owned by one user."""

    public_id: str
    user_id: int
    title: str | None
    status: TaskStatus
    priority: TaskPriority
    review_status: ReviewStatus
    reviewed_by: int | None
    reviewed_at: datetime | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class Material:
    """Metadata for an uploaded resume or JD material.

    The original file is deleted after successful parsing; only the SHA-256
    hash fingerprint is retained for deduplication and audit.
    """

    public_id: str
    task_id: int
    kind: MaterialKind
    original_filename: str
    file_hash: str
    file_size: int
    mime_type: str
    scan_status: ScanStatus
    original_deleted: bool
    deleted_at: datetime | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class AgentRun:
    """Auditable LangGraph run record."""

    public_id: str
    thread_id: str
    user_id: int
    workflow_version: str
    prompt_version: str
    status: RunStatus
    retry_count: int
    error_code: str | None
    error_summary: str | None
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class NodeRun:
    """Auditable LangGraph node execution record."""

    run_id: int
    node_name: str
    status: RunStatus
    duration_ms: int | None
    error_code: str | None
    metadata: dict[str, Any] | None
    started_at: datetime
    finished_at: datetime | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class ResumeStructure:
    """Versioned structured resume payload persisted after parsing.

    Sensitive attributes (age, gender, marital status, ethnicity, health,
    political status, photo, id card, hometown, religion, hukou) are never
    persisted; parser nodes must drop them before this entity is created.
    """

    task_id: int
    material_id: int
    version: int
    summary: str | None
    total_years_exp: float | None
    raw_structured: dict[str, Any]
    id: int | None = None


@dataclass(frozen=True, slots=True)
class SkillEvidence:
    """A single skill evidence row tied to a structured resume."""

    resume_structure_id: int
    skill_name: str
    evidence_snippet: str
    source_section: str | None
    proficiency: Proficiency | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class ExperienceEvidence:
    """A single work experience evidence row tied to a structured resume."""

    resume_structure_id: int
    role_title: str
    company_redacted: str | None
    duration_months: int | None
    evidence_snippet: str
    id: int | None = None


@dataclass(frozen=True, slots=True)
class EducationEvidence:
    """A single education evidence row tied to a structured resume."""

    resume_structure_id: int
    degree: Degree | None
    major: str | None
    school_tier: SchoolTier | None
    graduation_year: int | None
    evidence_snippet: str
    id: int | None = None


@dataclass(frozen=True, slots=True)
class JDStructure:
    """Versioned structured JD payload persisted after parsing."""

    task_id: int
    material_id: int
    version: int
    job_title: str | None
    summary: str | None
    raw_structured: dict[str, Any]
    id: int | None = None


@dataclass(frozen=True, slots=True)
class JDRequirement:
    """A single JD requirement row tied to a structured JD."""

    jd_structure_id: int
    requirement_type: RequirementType
    category: str | None
    text: str
    weight_hint: float | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Persisted match outcome between a resume structure and a JD structure.

    Sub-scores (``skill_score`` etc.) and ``overall_score`` are admin-only;
    regular users only see ``tier`` in API projections.
    """

    task_id: int
    resume_structure_id: int
    jd_structure_id: int
    tier: MatchTier
    prompt_version: str
    rule_version: str
    skill_score: float | None = None
    experience_score: float | None = None
    education_score: float | None = None
    soft_skill_score: float | None = None
    overall_score: float | None = None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class MatchItem:
    """A single JD requirement row mapped to resume evidence."""

    match_result_id: int
    requirement: str
    match_status: MatchTier
    evidence_snippet: str | None
    skill_category: SkillCategory | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class GapAnalysis:
    """A gap description tied to a match result, with an optional seed question."""

    match_result_id: int
    gap_description: str
    suggested_question: str | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class InterviewQuestion:
    """A structured interview question tied to a match result."""

    match_result_id: int
    question_text: str
    category: QuestionCategory
    difficulty: QuestionDifficulty | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class Report:
    """A recruitment analysis report tied to a task and its match result.

    Markdown is the canonical content; ``pdf_path`` is an optional generated
    artifact that may be regenerated on demand. ``expires_at`` enforces the
    data retention window — expired reports refuse download regardless of
    cache state.
    """

    public_id: str
    task_id: int
    match_result_id: int
    content_markdown: str
    created_by: int
    expires_at: datetime
    pdf_path: str | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class ManualOverride:
    """An admin-authored audit entry recording a single field change.

    ``field_path`` is a structured key (e.g. ``match_items[3].match_status``)
    that the API layer parses; ``old_value`` / ``new_value`` are stored as
    raw text to avoid coupling audit shape to schema drift.
    """

    match_result_id: int
    field_path: str
    reason: str
    admin_id: int
    old_value: str | None
    new_value: str | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class PromptVersion:
    """A versioned prompt template metadata row.

    ``template_key`` is a safe relative POSIX path resolved by the workflow
    Prompt loader (e.g. ``recruit_resume_parse/v3``). ``variables`` and
    ``output_schema`` are JSON blobs; the loader enforces shape at render
    time. ``status`` always starts as ``draft`` — promotion to ``active``
    or ``retired`` is owned by the admin API in RECRUIT-250.
    """

    public_id: str
    prompt_name: str
    version: str
    template_key: str
    status: PromptStatus
    created_by: int
    variables: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    id: int | None = None
