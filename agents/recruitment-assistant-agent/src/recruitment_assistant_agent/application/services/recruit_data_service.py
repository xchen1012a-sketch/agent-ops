"""Application use cases for RECRUIT-230 identity and data records."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from string import hexdigits
from typing import Any
from uuid import uuid4

from recruitment_assistant_agent.core.errors import AppError, ForbiddenError
from recruitment_assistant_agent.domain.entities.recruit_data import (
    AgentRun,
    EducationEvidence,
    ExperienceEvidence,
    GapAnalysis,
    InterviewQuestion,
    JDRequirement,
    JDStructure,
    ManualOverride,
    MatchItem,
    MatchResult,
    Material,
    NodeRun,
    PromptVersion,
    RecruitTask,
    Report,
    ResumeStructure,
    SkillEvidence,
    UserMirror,
)
from recruitment_assistant_agent.domain.ports.recruit_data_repository import (
    RecruitDataRepository,
)
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


class RecruitDataNotFoundError(AppError):
    """Raised when a required recruitment data record is absent."""

    code = "RECRUIT_DATA_NOT_FOUND"
    http_status = 404


def _validate_sha256(value: str, *, field_name: str) -> None:
    """Reject anything that is not a 64-character lowercase/uppercase hex string."""
    if len(value) != 64 or any(c not in hexdigits for c in value):
        raise ValueError(f"{field_name} must be a SHA-256 hexadecimal digest")


class RecruitDataService:
    """Coordinate RECRUIT-230 use cases without owning transaction commits."""

    def __init__(self, repository: RecruitDataRepository) -> None:
        self._repository = repository

    async def get_user_mirror(self, public_id: str) -> UserMirror:
        """Return a user mirror or raise when absent."""
        user = await self._repository.get_user_by_public_id(public_id)
        if user is None or user.id is None:
            raise RecruitDataNotFoundError("User mirror not found")
        return user

    async def sync_user_mirror(
        self,
        *,
        public_id: str,
        email: str,
        display_name: str | None,
        role: UserRole,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> UserMirror:
        """Create or update the local user mirror from trusted JWT claims."""
        return await self._repository.upsert_user_mirror(
            UserMirror(
                public_id=public_id,
                email=email,
                display_name=display_name,
                role=role,
                status=status,
            )
        )

    async def create_task(
        self,
        *,
        user_public_id: str,
        title: str | None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> RecruitTask:
        """Create a recruitment analysis task for an existing user."""
        user = await self.get_user_mirror(user_public_id)

        return await self._repository.create_task(
            RecruitTask(
                public_id=str(uuid4()),
                user_id=user.id or 0,
                title=title,
                status=TaskStatus.UPLOADED,
                priority=priority,
                review_status=ReviewStatus.PENDING,
                reviewed_by=None,
                reviewed_at=None,
            )
        )

    async def get_task_for_user(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
    ) -> RecruitTask:
        """Return a user-owned task or raise when absent/unauthorized."""
        user = await self.get_user_mirror(user_public_id)
        task = await self._repository.get_task_for_user(
            task_public_id=task_public_id,
            user_id=user.id or 0,
        )
        if task is None:
            raise RecruitDataNotFoundError("Recruitment task not found")
        return task

    async def register_material(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        kind: MaterialKind,
        original_filename: str,
        file_hash: str,
        file_size: int,
        mime_type: str,
    ) -> Material:
        """Register metadata for an uploaded resume or JD material.

        The original file lifecycle is owned by the file safety adapter; this
        method only persists the audit fingerprint. ``scan_status`` starts at
        ``pending`` and is updated by the file safety workflow node.
        """
        if file_size < 0:
            raise ValueError("file_size must be non-negative")
        _validate_sha256(file_hash, field_name="file_hash")
        if not original_filename:
            raise ValueError("original_filename must be non-empty")
        if not mime_type:
            raise ValueError("mime_type must be non-empty")

        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )

        return await self._repository.register_material(
            Material(
                public_id=str(uuid4()),
                task_id=task.id or 0,
                kind=kind,
                original_filename=original_filename,
                file_hash=file_hash.lower(),
                file_size=file_size,
                mime_type=mime_type,
                scan_status=ScanStatus.PENDING,
                original_deleted=False,
                deleted_at=None,
            )
        )

    async def get_material_for_task(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        material_public_id: str,
    ) -> Material:
        """Return a material scoped to a user-owned task, or raise."""
        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )
        material = await self._repository.get_material_for_task(
            material_public_id=material_public_id,
            task_id=task.id or 0,
        )
        if material is None:
            raise RecruitDataNotFoundError("Material not found")
        return material

    async def create_agent_run(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        workflow_version: str,
        prompt_version: str,
        started_at: datetime,
    ) -> AgentRun:
        """Create a pending audit record for a user-owned task."""
        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )

        return await self._repository.create_agent_run(
            AgentRun(
                public_id=str(uuid4()),
                thread_id=task_public_id,
                user_id=task.user_id,
                workflow_version=workflow_version,
                prompt_version=prompt_version,
                status=RunStatus.PENDING,
                retry_count=0,
                error_code=None,
                error_summary=None,
                started_at=started_at,
                finished_at=None,
                duration_ms=None,
            )
        )

    async def finish_agent_run(
        self,
        *,
        run: AgentRun,
        status: RunStatus,
        finished_at: datetime,
        duration_ms: int,
        error_code: str | None,
    ) -> AgentRun:
        """Persist the terminal status for an existing Agent run."""
        if run.id is None:
            raise ValueError("agent run id is required before finalizing workflow execution")
        return await self._repository.update_agent_run(
            replace(
                run,
                status=status,
                error_code=error_code,
                finished_at=finished_at,
                duration_ms=duration_ms,
            )
        )

    async def create_node_run(
        self,
        *,
        run_id: int,
        node_name: str,
        status: RunStatus,
        started_at: datetime,
        finished_at: datetime | None = None,
        duration_ms: int | None = None,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeRun:
        """Create a node run audit record for an existing Agent run."""
        return await self._repository.create_node_run(
            NodeRun(
                run_id=run_id,
                node_name=node_name,
                status=status,
                duration_ms=duration_ms,
                error_code=error_code,
                metadata=metadata,
                started_at=started_at,
                finished_at=finished_at,
            )
        )

    async def finish_node_run(
        self,
        *,
        node_run: NodeRun,
        status: RunStatus,
        finished_at: datetime,
        duration_ms: int,
        error_code: str | None,
        metadata: dict[str, Any],
    ) -> NodeRun:
        """Persist the terminal status for an existing node run."""
        if node_run.id is None:
            raise ValueError("node run id is required before finalizing workflow node")
        return await self._repository.update_node_run(
            replace(
                node_run,
                status=status,
                duration_ms=duration_ms,
                error_code=error_code,
                metadata=metadata,
                finished_at=finished_at,
            )
        )

    async def create_resume_structure(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        material_public_id: str,
        summary: str | None,
        total_years_exp: float | None,
        raw_structured: dict[str, Any],
    ) -> ResumeStructure:
        """Persist a new resume structure version scoped to a user-owned task.

        Sensitive attributes must already be stripped by the parser; this
        method does not inspect ``raw_structured`` for forbidden keys.
        Version is computed as max(existing) + 1 within the material scope.
        """
        if total_years_exp is not None and total_years_exp < 0:
            raise ValueError("total_years_exp must be non-negative")

        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )
        material = await self.get_material_for_task(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
            material_public_id=material_public_id,
        )
        if material.kind != MaterialKind.RESUME:
            raise ValueError("Material kind must be resume to attach resume structure")
        if material.task_id != task.id:
            raise RecruitDataNotFoundError("Material not found")

        next_version = await self._repository.get_max_resume_version(material.id or 0)
        return await self._repository.create_resume_structure(
            ResumeStructure(
                task_id=task.id or 0,
                material_id=material.id or 0,
                version=next_version + 1,
                summary=summary,
                total_years_exp=total_years_exp,
                raw_structured=raw_structured,
            )
        )

    async def get_latest_resume_structure_for_material(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        material_public_id: str,
    ) -> ResumeStructure | None:
        """Return the latest resume structure for a user-owned material, or None."""
        material = await self.get_material_for_task(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
            material_public_id=material_public_id,
        )
        if material.kind != MaterialKind.RESUME:
            raise ValueError("Material kind must be resume to query resume structure")
        return await self._repository.get_latest_resume_structure_for_material(
            material_id=material.id or 0,
        )

    async def append_skill_evidence(
        self,
        *,
        resume_structure: ResumeStructure,
        skill_name: str,
        evidence_snippet: str,
        source_section: str | None = None,
        proficiency: Proficiency | None = None,
    ) -> SkillEvidence:
        """Append a skill evidence row to an existing resume structure."""
        _validate_evidence(skill_name, evidence_snippet)
        return await self._repository.append_skill_evidence(
            SkillEvidence(
                resume_structure_id=resume_structure.id or 0,
                skill_name=skill_name,
                evidence_snippet=evidence_snippet,
                source_section=source_section,
                proficiency=proficiency,
            )
        )

    async def append_experience_evidence(
        self,
        *,
        resume_structure: ResumeStructure,
        role_title: str,
        evidence_snippet: str,
        company_redacted: str | None = None,
        duration_months: int | None = None,
    ) -> ExperienceEvidence:
        """Append a work experience evidence row to an existing resume structure."""
        _validate_evidence(role_title, evidence_snippet)
        if duration_months is not None and duration_months < 0:
            raise ValueError("duration_months must be non-negative")
        return await self._repository.append_experience_evidence(
            ExperienceEvidence(
                resume_structure_id=resume_structure.id or 0,
                role_title=role_title,
                company_redacted=company_redacted,
                duration_months=duration_months,
                evidence_snippet=evidence_snippet,
            )
        )

    async def append_education_evidence(
        self,
        *,
        resume_structure: ResumeStructure,
        evidence_snippet: str,
        degree: Degree | None = None,
        major: str | None = None,
        school_tier: SchoolTier | None = None,
        graduation_year: int | None = None,
    ) -> EducationEvidence:
        """Append an education evidence row to an existing resume structure."""
        if not evidence_snippet:
            raise ValueError("evidence_snippet must be non-empty")
        if graduation_year is not None and graduation_year < 1900:
            raise ValueError("graduation_year must be 1900 or later")
        return await self._repository.append_education_evidence(
            EducationEvidence(
                resume_structure_id=resume_structure.id or 0,
                degree=degree,
                major=major,
                school_tier=school_tier,
                graduation_year=graduation_year,
                evidence_snippet=evidence_snippet,
            )
        )

    async def create_jd_structure(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        material_public_id: str,
        job_title: str | None,
        summary: str | None,
        raw_structured: dict[str, Any],
    ) -> JDStructure:
        """Persist a new JD structure version scoped to a user-owned task.

        Version is computed as max(existing) + 1 within the material scope.
        """
        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )
        material = await self.get_material_for_task(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
            material_public_id=material_public_id,
        )
        if material.kind != MaterialKind.JD:
            raise ValueError("Material kind must be jd to attach jd structure")
        if material.task_id != task.id:
            raise RecruitDataNotFoundError("Material not found")

        next_version = await self._repository.get_max_jd_version(material.id or 0)
        return await self._repository.create_jd_structure(
            JDStructure(
                task_id=task.id or 0,
                material_id=material.id or 0,
                version=next_version + 1,
                job_title=job_title,
                summary=summary,
                raw_structured=raw_structured,
            )
        )

    async def get_latest_jd_structure_for_material(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        material_public_id: str,
    ) -> JDStructure | None:
        """Return the latest JD structure for a user-owned material, or None."""
        material = await self.get_material_for_task(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
            material_public_id=material_public_id,
        )
        if material.kind != MaterialKind.JD:
            raise ValueError("Material kind must be jd to query jd structure")
        return await self._repository.get_latest_jd_structure_for_material(
            material_id=material.id or 0,
        )

    async def append_jd_requirement(
        self,
        *,
        jd_structure: JDStructure,
        requirement_type: RequirementType,
        text: str,
        category: str | None = None,
        weight_hint: float | None = None,
    ) -> JDRequirement:
        """Append a JD requirement row to an existing JD structure."""
        if not text:
            raise ValueError("text must be non-empty")
        _validate_weight_hint(weight_hint)
        return await self._repository.append_jd_requirement(
            JDRequirement(
                jd_structure_id=jd_structure.id or 0,
                requirement_type=requirement_type,
                category=category,
                text=text,
                weight_hint=weight_hint,
            )
        )

    async def create_match_result(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        resume_structure: ResumeStructure,
        jd_structure: JDStructure,
        tier: MatchTier,
        prompt_version: str,
        rule_version: str,
        skill_score: float | None = None,
        experience_score: float | None = None,
        education_score: float | None = None,
        soft_skill_score: float | None = None,
        overall_score: float | None = None,
    ) -> MatchResult:
        """Persist a match result for a user-owned task's resume/JD pair.

        ``rule_version`` must be non-empty because it identifies the scoring
        rule source used to compute this result. Sub-scores are optional
        because partial matches may leave buckets unscored.
        """
        if not rule_version:
            raise ValueError("rule_version must be non-empty")
        if not prompt_version:
            raise ValueError("prompt_version must be non-empty")
        for name, value in (
            ("skill_score", skill_score),
            ("experience_score", experience_score),
            ("education_score", education_score),
            ("soft_skill_score", soft_skill_score),
            ("overall_score", overall_score),
        ):
            _validate_score(value, field_name=name)

        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )
        if resume_structure.task_id != task.id:
            raise RecruitDataNotFoundError("Resume structure not found for task")
        if jd_structure.task_id != task.id:
            raise RecruitDataNotFoundError("JD structure not found for task")

        existing = await self._repository.get_match_result_for_pair(
            resume_structure_id=resume_structure.id or 0,
            jd_structure_id=jd_structure.id or 0,
        )
        if existing is not None:
            raise ValueError("Match result already exists for this resume/JD pair")

        return await self._repository.create_match_result(
            MatchResult(
                task_id=task.id or 0,
                resume_structure_id=resume_structure.id or 0,
                jd_structure_id=jd_structure.id or 0,
                tier=tier,
                prompt_version=prompt_version,
                rule_version=rule_version,
                skill_score=skill_score,
                experience_score=experience_score,
                education_score=education_score,
                soft_skill_score=soft_skill_score,
                overall_score=overall_score,
            )
        )

    async def get_match_result_for_pair(
        self,
        *,
        resume_structure: ResumeStructure,
        jd_structure: JDStructure,
    ) -> MatchResult | None:
        """Return an existing match result for a resume/JD pair, or None."""
        return await self._repository.get_match_result_for_pair(
            resume_structure_id=resume_structure.id or 0,
            jd_structure_id=jd_structure.id or 0,
        )

    async def append_match_item(
        self,
        *,
        match_result: MatchResult,
        requirement: str,
        match_status: MatchTier,
        evidence_snippet: str | None = None,
        skill_category: SkillCategory | None = None,
    ) -> MatchItem:
        """Append a per-requirement match item to an existing match result.

        ``evidence_snippet`` must be empty when ``match_status`` is
        ``no_evidence``; this enforces the ADR-0009 invariant that no-evidence
        items must not be filled with candidate ability.
        """
        if not requirement:
            raise ValueError("requirement must be non-empty")
        if match_status is MatchTier.NO_EVIDENCE and evidence_snippet:
            raise ValueError("evidence_snippet must be empty when match_status is no_evidence")
        return await self._repository.append_match_item(
            MatchItem(
                match_result_id=match_result.id or 0,
                requirement=requirement,
                match_status=match_status,
                evidence_snippet=evidence_snippet,
                skill_category=skill_category,
            )
        )

    async def append_gap_analysis(
        self,
        *,
        match_result: MatchResult,
        gap_description: str,
        suggested_question: str | None = None,
    ) -> GapAnalysis:
        """Append a gap description with optional seed interview question."""
        if not gap_description:
            raise ValueError("gap_description must be non-empty")
        return await self._repository.append_gap_analysis(
            GapAnalysis(
                match_result_id=match_result.id or 0,
                gap_description=gap_description,
                suggested_question=suggested_question,
            )
        )

    async def append_interview_question(
        self,
        *,
        match_result: MatchResult,
        question_text: str,
        category: QuestionCategory,
        difficulty: QuestionDifficulty | None = None,
    ) -> InterviewQuestion:
        """Append a structured interview question to an existing match result."""
        if not question_text:
            raise ValueError("question_text must be non-empty")
        return await self._repository.append_interview_question(
            InterviewQuestion(
                match_result_id=match_result.id or 0,
                question_text=question_text,
                category=category,
                difficulty=difficulty,
            )
        )

    async def create_report(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
        match_result: MatchResult,
        content_markdown: str,
        created_by: int,
        expires_at: datetime,
        pdf_path: str | None = None,
    ) -> Report:
        """Persist a recruitment analysis report scoped to a user-owned task.

        ``expires_at`` must be in the future relative to ``created_by``'s
        ``created_at`` (enforced via service-level comparison against the
        provided ``expires_at`` argument); ``content_markdown`` may not be
        empty. ``pdf_path`` is optional and may be regenerated later.
        """
        if not content_markdown:
            raise ValueError("content_markdown must be non-empty")
        if created_by <= 0:
            raise ValueError("created_by must be a positive user id")
        if expires_at <= datetime.now(tz=expires_at.tzinfo):
            raise ValueError("expires_at must be in the future")

        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )
        if match_result.task_id != task.id:
            raise RecruitDataNotFoundError("Match result not found for task")

        return await self._repository.create_report(
            Report(
                public_id=str(uuid4()),
                task_id=task.id or 0,
                match_result_id=match_result.id or 0,
                content_markdown=content_markdown,
                pdf_path=pdf_path,
                created_by=created_by,
                expires_at=expires_at,
            )
        )

    async def get_report_for_task(
        self,
        *,
        user_public_id: str,
        task_public_id: str,
    ) -> Report | None:
        """Return the most recent report for a user-owned task, or None."""
        task = await self.get_task_for_user(
            user_public_id=user_public_id,
            task_public_id=task_public_id,
        )
        return await self._repository.get_report_for_task(task_id=task.id or 0)

    async def append_manual_override(
        self,
        *,
        match_result: MatchResult,
        field_path: str,
        reason: str,
        admin_id: int,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> ManualOverride:
        """Append an admin-authored override audit row to an existing match result.

        ``reason`` must be non-empty so the audit trail always explains why an
        admin edited a result. ``field_path`` must be non-empty; old/new values
        are free-form text to keep the audit shape decoupled from schema drift.
        """
        if not field_path:
            raise ValueError("field_path must be non-empty")
        if not reason:
            raise ValueError("reason must be non-empty")
        if admin_id <= 0:
            raise ValueError("admin_id must be a positive user id")
        return await self._repository.append_manual_override(
            ManualOverride(
                match_result_id=match_result.id or 0,
                field_path=field_path,
                old_value=old_value,
                new_value=new_value,
                reason=reason,
                admin_id=admin_id,
            )
        )

    async def create_prompt_version(
        self,
        *,
        creator: UserMirror,
        prompt_name: str,
        version: str,
        template_key: str,
        variables: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> PromptVersion:
        """Persist a new prompt version metadata row.

        Only administrators may create prompt versions; new versions always
        start as ``draft`` — activation / retirement is owned by the admin
        API in RECRUIT-250. ``template_key`` must be a safe relative POSIX
        key (no absolute paths, no ``..`` traversal, no Windows separators,
        no drive letters) so the workflow Prompt loader can resolve it
        without escaping the template root.
        """
        if creator.role is not UserRole.ADMIN:
            raise ForbiddenError("Only administrators can create prompt versions")
        if creator.id is None or creator.id <= 0:
            raise ValueError("creator must have a positive user id")
        if not prompt_name:
            raise ValueError("prompt_name must be non-empty")
        if not version:
            raise ValueError("version must be non-empty")
        _validate_template_key(template_key)

        existing = await self._repository.get_prompt_version(
            prompt_name=prompt_name,
            version=version,
        )
        if existing is not None:
            raise ValueError("Prompt version already exists for this name")

        return await self._repository.create_prompt_version(
            PromptVersion(
                public_id=str(uuid4()),
                prompt_name=prompt_name,
                version=version,
                template_key=template_key,
                variables=variables,
                output_schema=output_schema,
                status=PromptStatus.DRAFT,
                created_by=creator.id,
            )
        )

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        """Return a prompt version by (prompt_name, version), or None."""
        if not prompt_name:
            raise ValueError("prompt_name must be non-empty")
        if not version:
            raise ValueError("version must be non-empty")
        return await self._repository.get_prompt_version(
            prompt_name=prompt_name,
            version=version,
        )

    async def get_active_prompt_version(
        self,
        *,
        prompt_name: str,
    ) -> PromptVersion | None:
        """Return the currently active prompt version for a name, or None."""
        if not prompt_name:
            raise ValueError("prompt_name must be non-empty")
        return await self._repository.get_active_prompt_version(
            prompt_name=prompt_name,
        )


def _validate_evidence(name_field: str, evidence_snippet: str) -> None:
    """Reject empty name or evidence snippet values."""
    if not name_field:
        raise ValueError("name field must be non-empty")
    if not evidence_snippet:
        raise ValueError("evidence_snippet must be non-empty")


def _validate_weight_hint(value: float | None) -> None:
    """Reject weight_hint outside the 0.00 to 1.00 inclusive range."""
    if value is not None and not (0 <= value <= 1):
        raise ValueError("weight_hint must be between 0.00 and 1.00 inclusive")


def _validate_score(value: float | None, *, field_name: str) -> None:
    """Reject scores outside 0.00 to 100.00 inclusive (percent-style)."""
    if value is not None and not (0 <= value <= 100):
        raise ValueError(f"{field_name} must be between 0.00 and 100.00 inclusive")


def _validate_template_key(key: str) -> None:
    """Reject template_key values that escape the relative POSIX root.

    ``template_key`` is later resolved by the workflow Prompt loader against a
    trusted template directory. We refuse anything that could break out of
    that root: absolute paths, ``..`` traversal, Windows separators, and
    drive letters. Empty keys are also rejected.
    """
    if not key:
        raise ValueError("template_key must be non-empty")
    if "\\" in key:
        raise ValueError("template_key must not contain Windows separators")
    if key.startswith("/"):
        raise ValueError("template_key must be relative, not absolute")
    if len(key) >= 2 and key[1] == ":" and key[0].isalpha():
        raise ValueError("template_key must not contain drive letters")
    parts = key.split("/")
    if any(part == ".." for part in parts):
        raise ValueError("template_key must not contain parent traversal")
    if any(part == "" for part in parts[1:-1]):
        # Reject double-slashes inside the path; leading or trailing are tolerated
        # only when the caller explicitly uses them as namespace separators.
        raise ValueError("template_key must not contain empty path segments")
