"""SQLAlchemy repository for RECRUIT-230 identity and data records."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from recruitment_assistant_agent.domain.value_objects.recruit_enums import (
    PromptStatus,
)
from recruitment_assistant_agent.infrastructure.db.models.recruit_data import (
    AgentRunModel,
    EducationEvidenceModel,
    ExperienceEvidenceModel,
    GapAnalysisModel,
    InterviewQuestionModel,
    JDRequirementModel,
    JDStructureModel,
    ManualOverrideModel,
    MatchItemModel,
    MatchResultModel,
    MaterialModel,
    NodeRunModel,
    PromptVersionModel,
    RecruitTaskModel,
    ReportModel,
    ResumeStructureModel,
    SkillEvidenceModel,
    UserModel,
)


class SqlAlchemyRecruitDataRepository:
    """Persist RECRUIT-230 records using an externally managed session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_user_mirror(self, user: UserMirror) -> UserMirror:
        """Create or update a user mirror by public ID without committing."""
        existing = await self._get_user_model_by_public_id(user.public_id)
        if existing is None:
            existing = UserModel(
                public_id=user.public_id,
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                status=user.status,
            )
            self._session.add(existing)
        else:
            existing.email = user.email
            existing.display_name = user.display_name
            existing.role = user.role
            existing.status = user.status

        await self._session.flush()
        return self._to_user(existing)

    async def get_user_by_public_id(self, public_id: str) -> UserMirror | None:
        """Return a user mirror by public ID."""
        model = await self._get_user_model_by_public_id(public_id)
        return self._to_user(model) if model is not None else None

    async def create_task(self, task: RecruitTask) -> RecruitTask:
        """Persist a recruitment analysis task without committing."""
        model = RecruitTaskModel(
            public_id=task.public_id,
            user_id=task.user_id,
            title=task.title,
            status=task.status,
            priority=task.priority,
            review_status=task.review_status,
            reviewed_by=task.reviewed_by,
            reviewed_at=task.reviewed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_task(model)

    async def get_task_for_user(
        self,
        *,
        task_public_id: str,
        user_id: int,
    ) -> RecruitTask | None:
        """Return a user-owned task or None when absent/unauthorized."""
        result = await self._session.execute(
            select(RecruitTaskModel).where(
                RecruitTaskModel.public_id == task_public_id,
                RecruitTaskModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_task(model) if model is not None else None

    async def register_material(self, material: Material) -> Material:
        """Persist metadata for an uploaded resume or JD material."""
        model = MaterialModel(
            public_id=material.public_id,
            task_id=material.task_id,
            kind=material.kind,
            original_filename=material.original_filename,
            file_hash=material.file_hash,
            file_size=material.file_size,
            mime_type=material.mime_type,
            scan_status=material.scan_status,
            original_deleted=material.original_deleted,
            deleted_at=material.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_material(model)

    async def get_material_for_task(
        self,
        *,
        material_public_id: str,
        task_id: int,
    ) -> Material | None:
        """Return a material belonging to a task, or None."""
        result = await self._session.execute(
            select(MaterialModel).where(
                MaterialModel.public_id == material_public_id,
                MaterialModel.task_id == task_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_material(model) if model is not None else None

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        """Persist an Agent run audit record."""
        model = AgentRunModel(
            public_id=run.public_id,
            thread_id=run.thread_id,
            user_id=run.user_id,
            workflow_version=run.workflow_version,
            prompt_version=run.prompt_version,
            status=run.status,
            retry_count=run.retry_count,
            error_code=run.error_code,
            error_summary=run.error_summary,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_ms=run.duration_ms,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_agent_run(model)

    async def update_agent_run(self, run: AgentRun) -> AgentRun:
        """Update an existing Agent run audit record."""
        result = await self._session.execute(
            select(AgentRunModel).where(AgentRunModel.id == run.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Agent run not found")
        model.status = run.status
        model.retry_count = run.retry_count
        model.error_code = run.error_code
        model.error_summary = run.error_summary
        model.finished_at = run.finished_at
        model.duration_ms = run.duration_ms
        await self._session.flush()
        return self._to_agent_run(model)

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        """Persist an Agent node audit record."""
        model = NodeRunModel(
            run_id=node_run.run_id,
            node_name=node_run.node_name,
            status=node_run.status,
            duration_ms=node_run.duration_ms,
            error_code=node_run.error_code,
            metadata_json=node_run.metadata,
            started_at=node_run.started_at,
            finished_at=node_run.finished_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_node_run(model)

    async def update_node_run(self, node_run: NodeRun) -> NodeRun:
        """Update an existing Agent node audit record."""
        result = await self._session.execute(
            select(NodeRunModel).where(NodeRunModel.id == node_run.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Node run not found")
        model.status = node_run.status
        model.duration_ms = node_run.duration_ms
        model.error_code = node_run.error_code
        model.metadata_json = node_run.metadata
        model.finished_at = node_run.finished_at
        await self._session.flush()
        return self._to_node_run(model)

    async def create_resume_structure(self, structure: ResumeStructure) -> ResumeStructure:
        """Persist a new resume structure version for a task's material."""
        model = ResumeStructureModel(
            task_id=structure.task_id,
            material_id=structure.material_id,
            version=structure.version,
            summary=structure.summary,
            total_years_exp=structure.total_years_exp,
            raw_structured=structure.raw_structured,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_resume_structure(model)

    async def get_latest_resume_structure_for_material(
        self,
        *,
        material_id: int,
    ) -> ResumeStructure | None:
        """Return the highest-version resume structure for a material, or None."""
        result = await self._session.execute(
            select(ResumeStructureModel)
            .where(ResumeStructureModel.material_id == material_id)
            .order_by(
                ResumeStructureModel.version.desc(),
                ResumeStructureModel.id.desc(),
            )
            .limit(1),
        )
        model = result.scalar_one_or_none()
        return self._to_resume_structure(model) if model is not None else None

    async def get_resume_structure(
        self,
        *,
        resume_structure_id: int,
    ) -> ResumeStructure | None:
        """Return a resume structure by id, or None."""
        result = await self._session.execute(
            select(ResumeStructureModel).where(
                ResumeStructureModel.id == resume_structure_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_resume_structure(model) if model is not None else None

    async def append_skill_evidence(self, evidence: SkillEvidence) -> SkillEvidence:
        """Append a skill evidence row tied to a resume structure."""
        model = SkillEvidenceModel(
            resume_structure_id=evidence.resume_structure_id,
            skill_name=evidence.skill_name,
            evidence_snippet=evidence.evidence_snippet,
            source_section=evidence.source_section,
            proficiency=evidence.proficiency,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_skill_evidence(model)

    async def append_experience_evidence(
        self,
        evidence: ExperienceEvidence,
    ) -> ExperienceEvidence:
        """Append a work experience evidence row tied to a resume structure."""
        model = ExperienceEvidenceModel(
            resume_structure_id=evidence.resume_structure_id,
            role_title=evidence.role_title,
            company_redacted=evidence.company_redacted,
            duration_months=evidence.duration_months,
            evidence_snippet=evidence.evidence_snippet,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_experience_evidence(model)

    async def append_education_evidence(
        self,
        evidence: EducationEvidence,
    ) -> EducationEvidence:
        """Append an education evidence row tied to a resume structure."""
        model = EducationEvidenceModel(
            resume_structure_id=evidence.resume_structure_id,
            degree=evidence.degree,
            major=evidence.major,
            school_tier=evidence.school_tier,
            graduation_year=evidence.graduation_year,
            evidence_snippet=evidence.evidence_snippet,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_education_evidence(model)

    async def get_max_resume_version(self, material_id: int) -> int:
        """Return the max resume version for a material, or 0 if none exists."""
        result = await self._session.execute(
            select(func.max(ResumeStructureModel.version)).where(
                ResumeStructureModel.material_id == material_id,
            )
        )
        value = result.scalar_one()
        return int(value) if value is not None else 0

    async def create_jd_structure(self, structure: JDStructure) -> JDStructure:
        """Persist a new JD structure version for a task's material."""
        model = JDStructureModel(
            task_id=structure.task_id,
            material_id=structure.material_id,
            version=structure.version,
            job_title=structure.job_title,
            summary=structure.summary,
            raw_structured=structure.raw_structured,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_jd_structure(model)

    async def get_latest_jd_structure_for_material(
        self,
        *,
        material_id: int,
    ) -> JDStructure | None:
        """Return the highest-version JD structure for a material, or None."""
        result = await self._session.execute(
            select(JDStructureModel)
            .where(JDStructureModel.material_id == material_id)
            .order_by(
                JDStructureModel.version.desc(),
                JDStructureModel.id.desc(),
            )
            .limit(1),
        )
        model = result.scalar_one_or_none()
        return self._to_jd_structure(model) if model is not None else None

    async def append_jd_requirement(self, requirement: JDRequirement) -> JDRequirement:
        """Append a JD requirement row to an existing JD structure."""
        model = JDRequirementModel(
            jd_structure_id=requirement.jd_structure_id,
            requirement_type=requirement.requirement_type,
            category=requirement.category,
            text=requirement.text,
            weight_hint=requirement.weight_hint,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_jd_requirement(model)

    async def get_max_jd_version(self, material_id: int) -> int:
        """Return the max JD version for a material, or 0 if none exists."""
        result = await self._session.execute(
            select(func.max(JDStructureModel.version)).where(
                JDStructureModel.material_id == material_id,
            )
        )
        value = result.scalar_one()
        return int(value) if value is not None else 0

    async def create_match_result(self, result: MatchResult) -> MatchResult:
        """Persist a match result for a resume/JD structure pair."""
        model = MatchResultModel(
            task_id=result.task_id,
            resume_structure_id=result.resume_structure_id,
            jd_structure_id=result.jd_structure_id,
            skill_score=result.skill_score,
            experience_score=result.experience_score,
            education_score=result.education_score,
            soft_skill_score=result.soft_skill_score,
            overall_score=result.overall_score,
            tier=result.tier,
            prompt_version=result.prompt_version,
            rule_version=result.rule_version,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_match_result(model)

    async def get_match_result_for_pair(
        self,
        *,
        resume_structure_id: int,
        jd_structure_id: int,
    ) -> MatchResult | None:
        """Return an existing match result for a resume/JD pair, or None."""
        result = await self._session.execute(
            select(MatchResultModel).where(
                MatchResultModel.resume_structure_id == resume_structure_id,
                MatchResultModel.jd_structure_id == jd_structure_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_match_result(model) if model is not None else None

    async def append_match_item(self, item: MatchItem) -> MatchItem:
        """Append a per-requirement match item to an existing match result."""
        model = MatchItemModel(
            match_result_id=item.match_result_id,
            requirement=item.requirement,
            match_status=item.match_status,
            evidence_snippet=item.evidence_snippet,
            skill_category=item.skill_category,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_match_item(model)

    async def append_gap_analysis(self, gap: GapAnalysis) -> GapAnalysis:
        """Append a gap analysis row tied to an existing match result."""
        model = GapAnalysisModel(
            match_result_id=gap.match_result_id,
            gap_description=gap.gap_description,
            suggested_question=gap.suggested_question,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_gap_analysis(model)

    async def append_interview_question(
        self,
        question: InterviewQuestion,
    ) -> InterviewQuestion:
        """Append a structured interview question to an existing match result."""
        model = InterviewQuestionModel(
            match_result_id=question.match_result_id,
            question_text=question.question_text,
            category=question.category,
            difficulty=question.difficulty,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_interview_question(model)

    async def create_report(self, report: Report) -> Report:
        """Persist a recruitment analysis report."""
        model = ReportModel(
            public_id=report.public_id,
            task_id=report.task_id,
            match_result_id=report.match_result_id,
            content_markdown=report.content_markdown,
            pdf_path=report.pdf_path,
            created_by=report.created_by,
            expires_at=report.expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_report(model)

    async def get_report_for_task(
        self,
        *,
        task_id: int,
    ) -> Report | None:
        """Return the most recently created report for a task, or None."""
        result = await self._session.execute(
            select(ReportModel)
            .where(ReportModel.task_id == task_id)
            .order_by(
                ReportModel.created_at.desc(),
                ReportModel.id.desc(),
            )
            .limit(1),
        )
        model = result.scalar_one_or_none()
        return self._to_report(model) if model is not None else None

    async def append_manual_override(
        self,
        override: ManualOverride,
    ) -> ManualOverride:
        """Append an admin-authored override audit row to a match result."""
        model = ManualOverrideModel(
            match_result_id=override.match_result_id,
            field_path=override.field_path,
            old_value=override.old_value,
            new_value=override.new_value,
            reason=override.reason,
            admin_id=override.admin_id,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_manual_override(model)

    async def create_prompt_version(self, prompt: PromptVersion) -> PromptVersion:
        """Persist a new prompt version row."""
        model = PromptVersionModel(
            public_id=prompt.public_id,
            prompt_name=prompt.prompt_name,
            version=prompt.version,
            template_key=prompt.template_key,
            variables=prompt.variables,
            output_schema=prompt.output_schema,
            status=prompt.status,
            created_by=prompt.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_prompt_version(model)

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        """Return a prompt version by (prompt_name, version), or None."""
        result = await self._session.execute(
            select(PromptVersionModel).where(
                PromptVersionModel.prompt_name == prompt_name,
                PromptVersionModel.version == version,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_prompt_version(model) if model is not None else None

    async def get_active_prompt_version(
        self,
        *,
        prompt_name: str,
    ) -> PromptVersion | None:
        """Return the currently active prompt version for a name, or None."""
        result = await self._session.execute(
            select(PromptVersionModel)
            .where(
                PromptVersionModel.prompt_name == prompt_name,
                PromptVersionModel.status == PromptStatus.ACTIVE,
            )
            .order_by(
                PromptVersionModel.created_at.desc(),
                PromptVersionModel.id.desc(),
            )
            .limit(1),
        )
        model = result.scalar_one_or_none()
        return self._to_prompt_version(model) if model is not None else None

    async def _get_user_model_by_public_id(self, public_id: str) -> UserModel | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.public_id == public_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_user(model: UserModel) -> UserMirror:
        return UserMirror(
            id=model.id,
            public_id=model.public_id,
            email=model.email,
            display_name=model.display_name,
            role=model.role,
            status=model.status,
        )

    @staticmethod
    def _to_task(model: RecruitTaskModel) -> RecruitTask:
        return RecruitTask(
            id=model.id,
            public_id=model.public_id,
            user_id=model.user_id,
            title=model.title,
            status=model.status,
            priority=model.priority,
            review_status=model.review_status,
            reviewed_by=model.reviewed_by,
            reviewed_at=model.reviewed_at,
        )

    @staticmethod
    def _to_material(model: MaterialModel) -> Material:
        return Material(
            id=model.id,
            public_id=model.public_id,
            task_id=model.task_id,
            kind=model.kind,
            original_filename=model.original_filename,
            file_hash=model.file_hash,
            file_size=model.file_size,
            mime_type=model.mime_type,
            scan_status=model.scan_status,
            original_deleted=model.original_deleted,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _to_agent_run(model: AgentRunModel) -> AgentRun:
        return AgentRun(
            id=model.id,
            public_id=model.public_id,
            thread_id=model.thread_id,
            user_id=model.user_id,
            workflow_version=model.workflow_version,
            prompt_version=model.prompt_version,
            status=model.status,
            retry_count=model.retry_count,
            error_code=model.error_code,
            error_summary=model.error_summary,
            started_at=model.started_at,
            finished_at=model.finished_at,
            duration_ms=model.duration_ms,
        )

    @staticmethod
    def _to_node_run(model: NodeRunModel) -> NodeRun:
        return NodeRun(
            id=model.id,
            run_id=model.run_id,
            node_name=model.node_name,
            status=model.status,
            duration_ms=model.duration_ms,
            error_code=model.error_code,
            metadata=model.metadata_json,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )

    @staticmethod
    def _to_resume_structure(model: ResumeStructureModel) -> ResumeStructure:
        total_years_exp = (
            float(model.total_years_exp) if model.total_years_exp is not None else None
        )
        return ResumeStructure(
            id=model.id,
            task_id=model.task_id,
            material_id=model.material_id,
            version=model.version,
            summary=model.summary,
            total_years_exp=total_years_exp,
            raw_structured=model.raw_structured,
        )

    @staticmethod
    def _to_skill_evidence(model: SkillEvidenceModel) -> SkillEvidence:
        return SkillEvidence(
            id=model.id,
            resume_structure_id=model.resume_structure_id,
            skill_name=model.skill_name,
            evidence_snippet=model.evidence_snippet,
            source_section=model.source_section,
            proficiency=model.proficiency,
        )

    @staticmethod
    def _to_experience_evidence(model: ExperienceEvidenceModel) -> ExperienceEvidence:
        return ExperienceEvidence(
            id=model.id,
            resume_structure_id=model.resume_structure_id,
            role_title=model.role_title,
            company_redacted=model.company_redacted,
            duration_months=model.duration_months,
            evidence_snippet=model.evidence_snippet,
        )

    @staticmethod
    def _to_education_evidence(model: EducationEvidenceModel) -> EducationEvidence:
        return EducationEvidence(
            id=model.id,
            resume_structure_id=model.resume_structure_id,
            degree=model.degree,
            major=model.major,
            school_tier=model.school_tier,
            graduation_year=model.graduation_year,
            evidence_snippet=model.evidence_snippet,
        )

    @staticmethod
    def _to_jd_structure(model: JDStructureModel) -> JDStructure:
        return JDStructure(
            id=model.id,
            task_id=model.task_id,
            material_id=model.material_id,
            version=model.version,
            job_title=model.job_title,
            summary=model.summary,
            raw_structured=model.raw_structured,
        )

    @staticmethod
    def _to_jd_requirement(model: JDRequirementModel) -> JDRequirement:
        weight_hint = float(model.weight_hint) if model.weight_hint is not None else None
        return JDRequirement(
            id=model.id,
            jd_structure_id=model.jd_structure_id,
            requirement_type=model.requirement_type,
            category=model.category,
            text=model.text_content,
            weight_hint=weight_hint,
        )

    @staticmethod
    def _to_match_result(model: MatchResultModel) -> MatchResult:
        def _score(value: float | None) -> float | None:
            return value if value is not None else None

        return MatchResult(
            id=model.id,
            task_id=model.task_id,
            resume_structure_id=model.resume_structure_id,
            jd_structure_id=model.jd_structure_id,
            tier=model.tier,
            prompt_version=model.prompt_version,
            rule_version=model.rule_version,
            skill_score=_score(model.skill_score),
            experience_score=_score(model.experience_score),
            education_score=_score(model.education_score),
            soft_skill_score=_score(model.soft_skill_score),
            overall_score=_score(model.overall_score),
        )

    @staticmethod
    def _to_match_item(model: MatchItemModel) -> MatchItem:
        return MatchItem(
            id=model.id,
            match_result_id=model.match_result_id,
            requirement=model.requirement,
            match_status=model.match_status,
            evidence_snippet=model.evidence_snippet,
            skill_category=model.skill_category,
        )

    @staticmethod
    def _to_gap_analysis(model: GapAnalysisModel) -> GapAnalysis:
        return GapAnalysis(
            id=model.id,
            match_result_id=model.match_result_id,
            gap_description=model.gap_description,
            suggested_question=model.suggested_question,
        )

    @staticmethod
    def _to_interview_question(model: InterviewQuestionModel) -> InterviewQuestion:
        return InterviewQuestion(
            id=model.id,
            match_result_id=model.match_result_id,
            question_text=model.question_text,
            category=model.category,
            difficulty=model.difficulty,
        )

    @staticmethod
    def _to_report(model: ReportModel) -> Report:
        return Report(
            id=model.id,
            public_id=model.public_id,
            task_id=model.task_id,
            match_result_id=model.match_result_id,
            content_markdown=model.content_markdown,
            pdf_path=model.pdf_path,
            created_by=model.created_by,
            expires_at=model.expires_at,
        )

    @staticmethod
    def _to_manual_override(model: ManualOverrideModel) -> ManualOverride:
        return ManualOverride(
            id=model.id,
            match_result_id=model.match_result_id,
            field_path=model.field_path,
            old_value=model.old_value,
            new_value=model.new_value,
            reason=model.reason,
            admin_id=model.admin_id,
        )

    @staticmethod
    def _to_prompt_version(model: PromptVersionModel) -> PromptVersion:
        return PromptVersion(
            id=model.id,
            public_id=model.public_id,
            prompt_name=model.prompt_name,
            version=model.version,
            template_key=model.template_key,
            variables=model.variables,
            output_schema=model.output_schema,
            status=model.status,
            created_by=model.created_by,
        )
