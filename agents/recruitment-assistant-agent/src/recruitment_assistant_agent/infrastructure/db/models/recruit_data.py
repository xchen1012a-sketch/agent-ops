"""ORM models for the RECRUIT-230 identity and data layer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
from recruitment_assistant_agent.infrastructure.db.base import Base

UnsignedBigInteger = mysql.BIGINT(unsigned=True)
DateTimeFsp = mysql.DATETIME(fsp=6)


def _enum_values(
    enum_cls: type[UserRole]
    | type[UserStatus]
    | type[TaskStatus]
    | type[TaskPriority]
    | type[ReviewStatus]
    | type[MaterialKind]
    | type[ScanStatus]
    | type[RunStatus]
    | type[Proficiency]
    | type[Degree]
    | type[SchoolTier]
    | type[RequirementType]
    | type[MatchTier]
    | type[SkillCategory]
    | type[QuestionCategory]
    | type[QuestionDifficulty]
    | type[PromptStatus],
) -> list[str]:
    return [member.value for member in enum_cls]


class TimestampMixin:
    """Common MySQL datetime columns for mutable business rows."""

    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )


class UserModel(TimestampMixin, Base):
    """Recruitment service mirror of a unified-auth user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=_enum_values, name="user_role"),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, values_callable=_enum_values, name="user_status"),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )

    tasks: Mapped[list[RecruitTaskModel]] = relationship(
        back_populates="user",
        foreign_keys="RecruitTaskModel.user_id",
    )


class RecruitTaskModel(TimestampMixin, Base):
    """Recruitment analysis task owned by one user."""

    __tablename__ = "tasks"
    __table_args__ = (
        Index("idx_tasks_user_time", "user_id", "created_at"),
        Index("idx_tasks_review", "review_status", "created_at"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_tasks_user"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, values_callable=_enum_values, name="task_status"),
        nullable=False,
        default=TaskStatus.UPLOADED,
        server_default=TaskStatus.UPLOADED.value,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority, values_callable=_enum_values, name="task_priority"),
        nullable=False,
        default=TaskPriority.NORMAL,
        server_default=TaskPriority.NORMAL.value,
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, values_callable=_enum_values, name="review_status"),
        nullable=False,
        default=ReviewStatus.PENDING,
        server_default=ReviewStatus.PENDING.value,
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_tasks_reviewer"),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTimeFsp)

    user: Mapped[UserModel] = relationship(
        back_populates="tasks",
        foreign_keys=[user_id],
    )
    reviewer: Mapped[UserModel | None] = relationship(foreign_keys=[reviewed_by])
    materials: Mapped[list[MaterialModel]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )


class MaterialModel(Base):
    """Metadata for an uploaded resume or JD material."""

    __tablename__ = "materials"
    __table_args__ = (
        Index("idx_materials_hash", "file_hash"),
        Index("idx_materials_task", "task_id"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    task_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("tasks.id", name="fk_materials_task", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[MaterialKind] = mapped_column(
        SAEnum(MaterialKind, values_callable=_enum_values, name="material_kind"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(mysql.CHAR(64), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scan_status: Mapped[ScanStatus] = mapped_column(
        SAEnum(ScanStatus, values_callable=_enum_values, name="scan_status"),
        nullable=False,
        default=ScanStatus.PENDING,
        server_default=ScanStatus.PENDING.value,
    )
    original_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTimeFsp)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    task: Mapped[RecruitTaskModel] = relationship(back_populates="materials")
    resume_structures: Mapped[list[ResumeStructureModel]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )
    jd_structures: Mapped[list[JDStructureModel]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
    )


class AgentRunModel(Base):
    """Auditable Agent run record."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("idx_runs_thread", "thread_id", "started_at"),
        Index("idx_runs_status", "status"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    thread_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False)
    user_id: Mapped[int] = mapped_column(UnsignedBigInteger, nullable=False)
    workflow_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, values_callable=_enum_values, name="run_status"),
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTimeFsp, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTimeFsp)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    node_runs: Mapped[list[NodeRunModel]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class NodeRunModel(Base):
    """Auditable LangGraph node execution record."""

    __tablename__ = "node_runs"
    __table_args__ = (Index("idx_node_runs_run", "run_id", "started_at"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("agent_runs.id", name="fk_node_run", ondelete="CASCADE"),
        nullable=False,
    )
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, values_callable=_enum_values, name="node_run_status"),
        nullable=False,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    started_at: Mapped[datetime] = mapped_column(DateTimeFsp, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTimeFsp)

    run: Mapped[AgentRunModel] = relationship(back_populates="node_runs")


class ResumeStructureModel(Base):
    """Versioned structured resume payload."""

    __tablename__ = "resume_structures"
    __table_args__ = (
        UniqueConstraint(
            "material_id",
            "version",
            name="uq_resume_structures_material_version",
        ),
        Index("idx_resume_structures_material_version", "material_id", "version"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("tasks.id", name="fk_resume_structures_task", ondelete="CASCADE"),
        nullable=False,
    )
    material_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("materials.id", name="fk_resume_structures_material", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    total_years_exp: Mapped[float | None] = mapped_column(Numeric(5, 1))
    raw_structured: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    material: Mapped[MaterialModel] = relationship(back_populates="resume_structures")
    skill_evidence: Mapped[list[SkillEvidenceModel]] = relationship(
        back_populates="resume_structure",
        cascade="all, delete-orphan",
    )
    experience_evidence: Mapped[list[ExperienceEvidenceModel]] = relationship(
        back_populates="resume_structure",
        cascade="all, delete-orphan",
    )
    education_evidence: Mapped[list[EducationEvidenceModel]] = relationship(
        back_populates="resume_structure",
        cascade="all, delete-orphan",
    )


class SkillEvidenceModel(Base):
    """Skill evidence row tied to a structured resume."""

    __tablename__ = "skill_evidence"
    __table_args__ = (Index("idx_skill_evidence_structure", "resume_structure_id"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    resume_structure_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "resume_structures.id",
            name="fk_skill_evidence_structure",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    source_section: Mapped[str | None] = mapped_column(String(100))
    proficiency: Mapped[Proficiency | None] = mapped_column(
        SAEnum(Proficiency, values_callable=_enum_values, name="proficiency"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    resume_structure: Mapped[ResumeStructureModel] = relationship(
        back_populates="skill_evidence",
    )


class ExperienceEvidenceModel(Base):
    """Work experience evidence row tied to a structured resume."""

    __tablename__ = "experience_evidence"
    __table_args__ = (Index("idx_experience_evidence_structure", "resume_structure_id"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    resume_structure_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "resume_structures.id",
            name="fk_experience_evidence_structure",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    role_title: Mapped[str] = mapped_column(String(100), nullable=False)
    company_redacted: Mapped[str | None] = mapped_column(String(100))
    duration_months: Mapped[int | None] = mapped_column(Integer)
    evidence_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    resume_structure: Mapped[ResumeStructureModel] = relationship(
        back_populates="experience_evidence",
    )


class EducationEvidenceModel(Base):
    """Education evidence row tied to a structured resume."""

    __tablename__ = "education_evidence"
    __table_args__ = (Index("idx_education_evidence_structure", "resume_structure_id"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    resume_structure_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "resume_structures.id",
            name="fk_education_evidence_structure",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    degree: Mapped[Degree | None] = mapped_column(
        SAEnum(Degree, values_callable=_enum_values, name="degree"),
    )
    major: Mapped[str | None] = mapped_column(String(100))
    school_tier: Mapped[SchoolTier | None] = mapped_column(
        SAEnum(SchoolTier, values_callable=_enum_values, name="school_tier"),
    )
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    evidence_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    resume_structure: Mapped[ResumeStructureModel] = relationship(
        back_populates="education_evidence",
    )


class JDStructureModel(Base):
    """Versioned structured JD payload."""

    __tablename__ = "jd_structures"
    __table_args__ = (
        UniqueConstraint(
            "material_id",
            "version",
            name="uq_jd_structures_material_version",
        ),
        Index("idx_jd_structures_material_version", "material_id", "version"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("tasks.id", name="fk_jd_structures_task", ondelete="CASCADE"),
        nullable=False,
    )
    material_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("materials.id", name="fk_jd_structures_material", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    raw_structured: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    material: Mapped[MaterialModel] = relationship(back_populates="jd_structures")
    requirements: Mapped[list[JDRequirementModel]] = relationship(
        back_populates="jd_structure",
        cascade="all, delete-orphan",
    )


class JDRequirementModel(Base):
    """A single JD requirement row tied to a structured JD."""

    __tablename__ = "jd_requirements"
    __table_args__ = (Index("idx_jd_requirements_structure", "jd_structure_id"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    jd_structure_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "jd_structures.id",
            name="fk_jd_requirements_structure",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    requirement_type: Mapped[RequirementType] = mapped_column(
        SAEnum(
            RequirementType,
            values_callable=_enum_values,
            name="requirement_type",
        ),
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(String(100))
    text_content: Mapped[str] = mapped_column("text", Text, nullable=False)
    weight_hint: Mapped[float | None] = mapped_column(Numeric(3, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    jd_structure: Mapped[JDStructureModel] = relationship(
        back_populates="requirements",
    )


class MatchResultModel(Base):
    """Persisted match outcome between a resume structure and a JD structure."""

    __tablename__ = "match_results"
    __table_args__ = (
        UniqueConstraint(
            "resume_structure_id",
            "jd_structure_id",
            name="uk_match_pair",
        ),
        Index("idx_match_results_task", "task_id"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("tasks.id", name="fk_match_task", ondelete="CASCADE"),
        nullable=False,
    )
    resume_structure_id: Mapped[int] = mapped_column(UnsignedBigInteger, nullable=False)
    jd_structure_id: Mapped[int] = mapped_column(UnsignedBigInteger, nullable=False)
    skill_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    experience_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    education_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    soft_skill_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    overall_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    tier: Mapped[MatchTier] = mapped_column(
        SAEnum(MatchTier, values_callable=_enum_values, name="match_tier"),
        nullable=False,
    )
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    items: Mapped[list[MatchItemModel]] = relationship(
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    gap_analyses: Mapped[list[GapAnalysisModel]] = relationship(
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    interview_questions: Mapped[list[InterviewQuestionModel]] = relationship(
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list[ReportModel]] = relationship(
        back_populates="match_result",
        cascade="all, delete-orphan",
    )
    manual_overrides: Mapped[list[ManualOverrideModel]] = relationship(
        back_populates="match_result",
        cascade="all, delete-orphan",
    )


class MatchItemModel(Base):
    """A single JD requirement row mapped to resume evidence."""

    __tablename__ = "match_items"
    __table_args__ = (Index("idx_match_items_result", "match_result_id"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    match_result_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "match_results.id",
            name="fk_item_match",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    requirement: Mapped[str] = mapped_column(String(255), nullable=False)
    match_status: Mapped[MatchTier] = mapped_column(
        SAEnum(
            MatchTier,
            values_callable=_enum_values,
            name="match_status",
        ),
        nullable=False,
    )
    evidence_snippet: Mapped[str | None] = mapped_column(Text)
    skill_category: Mapped[SkillCategory | None] = mapped_column(
        SAEnum(
            SkillCategory,
            values_callable=_enum_values,
            name="skill_category",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    match_result: Mapped[MatchResultModel] = relationship(back_populates="items")


class GapAnalysisModel(Base):
    """A gap description tied to a match result, with an optional seed question."""

    __tablename__ = "gap_analyses"
    __table_args__ = (Index("idx_gap_analyses_match", "match_result_id"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    match_result_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "match_results.id",
            name="fk_gap_match",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    gap_description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_question: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    match_result: Mapped[MatchResultModel] = relationship(
        back_populates="gap_analyses",
    )


class InterviewQuestionModel(Base):
    """A structured interview question tied to a match result."""

    __tablename__ = "interview_questions"
    __table_args__ = (Index("idx_interview_questions_match", "match_result_id"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    match_result_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "match_results.id",
            name="fk_q_match",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[QuestionCategory] = mapped_column(
        SAEnum(
            QuestionCategory,
            values_callable=_enum_values,
            name="question_category",
        ),
        nullable=False,
    )
    difficulty: Mapped[QuestionDifficulty | None] = mapped_column(
        SAEnum(
            QuestionDifficulty,
            values_callable=_enum_values,
            name="question_difficulty",
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    match_result: Mapped[MatchResultModel] = relationship(
        back_populates="interview_questions",
    )


class ReportModel(Base):
    """A recruitment analysis report tied to a task and its match result."""

    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("public_id", name="uk_reports_public_id"),
        Index("idx_reports_task", "task_id"),
        Index("idx_reports_match", "match_result_id"),
        Index("idx_reports_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False)
    task_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("tasks.id", name="fk_reports_task", ondelete="CASCADE"),
        nullable=False,
    )
    match_result_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "match_results.id",
            name="fk_reports_match",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_reports_creator"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTimeFsp, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    task: Mapped[RecruitTaskModel] = relationship()
    match_result: Mapped[MatchResultModel] = relationship(
        back_populates="reports",
    )
    creator: Mapped[UserModel] = relationship(foreign_keys=[created_by])


class ManualOverrideModel(Base):
    """An admin-authored audit entry recording a single field change."""

    __tablename__ = "manual_overrides"
    __table_args__ = (
        Index("idx_manual_overrides_match", "match_result_id"),
        Index("idx_manual_overrides_admin", "admin_id"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    match_result_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey(
            "match_results.id",
            name="fk_override_match",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    field_path: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    admin_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_override_admin"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    match_result: Mapped[MatchResultModel] = relationship(
        back_populates="manual_overrides",
    )
    admin: Mapped[UserModel] = relationship(foreign_keys=[admin_id])


class PromptVersionModel(Base):
    """A versioned prompt template metadata row.

    Status transitions are owned by the admin API; this table records only
    the metadata needed by the workflow Prompt loader to render a template.
    """

    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint(
            "prompt_name",
            "version",
            name="uk_prompt_name_version",
        ),
        Index("idx_prompt_versions_name_status", "prompt_name", "status"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False)
    prompt_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    template_key: Mapped[str] = mapped_column(String(255), nullable=False)
    variables: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[PromptStatus] = mapped_column(
        SAEnum(
            PromptStatus,
            values_callable=_enum_values,
            name="prompt_status",
        ),
        nullable=False,
        default=PromptStatus.DRAFT,
        server_default=PromptStatus.DRAFT.value,
    )
    created_by: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_prompt_creator"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    creator: Mapped[UserModel] = relationship(foreign_keys=[created_by])
