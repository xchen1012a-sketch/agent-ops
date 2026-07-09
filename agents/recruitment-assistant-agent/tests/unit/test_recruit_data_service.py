"""Unit tests for RECRUIT-230 application services."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest

from recruitment_assistant_agent.application.services import (
    RecruitDataNotFoundError,
    RecruitDataService,
)
from recruitment_assistant_agent.core.errors import ForbiddenError
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

VALID_SHA256_A = "a" * 64
VALID_SHA256_B = "b" * 64


class FakeRecruitDataRepository:
    """In-memory repository test double that never commits transactions."""

    def __init__(self) -> None:
        self.user: UserMirror | None = None
        self.task: RecruitTask | None = None
        self.materials: list[Material] = []
        self.agent_runs: list[AgentRun] = []
        self.node_runs: list[NodeRun] = []
        self.resume_structures: list[ResumeStructure] = []
        self.skill_evidence: list[SkillEvidence] = []
        self.experience_evidence: list[ExperienceEvidence] = []
        self.education_evidence: list[EducationEvidence] = []
        self.jd_structures: list[JDStructure] = []
        self.jd_requirements: list[JDRequirement] = []
        self.match_results: list[MatchResult] = []
        self.match_items: list[MatchItem] = []
        self.gap_analyses: list[GapAnalysis] = []
        self.interview_questions: list[InterviewQuestion] = []
        self.reports: list[Report] = []
        self.manual_overrides: list[ManualOverride] = []
        self.prompt_versions: list[PromptVersion] = []

    async def upsert_user_mirror(self, user: UserMirror) -> UserMirror:
        self.user = UserMirror(
            id=1,
            public_id=user.public_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            status=user.status,
        )
        return self.user

    async def get_user_by_public_id(self, public_id: str) -> UserMirror | None:
        if self.user is None or self.user.public_id != public_id:
            return None
        return self.user

    async def create_task(self, task: RecruitTask) -> RecruitTask:
        self.task = RecruitTask(
            id=10,
            public_id=task.public_id,
            user_id=task.user_id,
            title=task.title,
            status=task.status,
            priority=task.priority,
            review_status=task.review_status,
            reviewed_by=task.reviewed_by,
            reviewed_at=task.reviewed_at,
        )
        return self.task

    async def get_task_for_user(
        self,
        *,
        task_public_id: str,
        user_id: int,
    ) -> RecruitTask | None:
        if (
            self.task is None
            or self.task.public_id != task_public_id
            or self.task.user_id != user_id
        ):
            return None
        return self.task

    async def register_material(self, material: Material) -> Material:
        persisted = Material(
            id=20 + len(self.materials),
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
        self.materials.append(persisted)
        return persisted

    async def get_material_for_task(
        self,
        *,
        material_public_id: str,
        task_id: int,
    ) -> Material | None:
        for material in self.materials:
            if material.public_id == material_public_id and material.task_id == task_id:
                return material
        return None

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        persisted = AgentRun(
            id=30 + len(self.agent_runs),
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
        self.agent_runs.append(persisted)
        return persisted

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        persisted = NodeRun(
            id=40 + len(self.node_runs),
            run_id=node_run.run_id,
            node_name=node_run.node_name,
            status=node_run.status,
            duration_ms=node_run.duration_ms,
            error_code=node_run.error_code,
            metadata=node_run.metadata,
            started_at=node_run.started_at,
            finished_at=node_run.finished_at,
        )
        self.node_runs.append(persisted)
        return persisted

    async def create_resume_structure(self, structure: ResumeStructure) -> ResumeStructure:
        persisted = ResumeStructure(
            id=50 + len(self.resume_structures),
            task_id=structure.task_id,
            material_id=structure.material_id,
            version=structure.version,
            summary=structure.summary,
            total_years_exp=structure.total_years_exp,
            raw_structured=structure.raw_structured,
        )
        self.resume_structures.append(persisted)
        return persisted

    async def get_latest_resume_structure_for_material(
        self,
        *,
        material_id: int,
    ) -> ResumeStructure | None:
        matching = [r for r in self.resume_structures if r.material_id == material_id]
        if not matching:
            return None
        return max(matching, key=lambda r: (r.version, r.id or 0))

    async def get_resume_structure(
        self,
        *,
        resume_structure_id: int,
    ) -> ResumeStructure | None:
        for structure in self.resume_structures:
            if structure.id == resume_structure_id:
                return structure
        return None

    async def append_skill_evidence(self, evidence: SkillEvidence) -> SkillEvidence:
        persisted = SkillEvidence(
            id=60 + len(self.skill_evidence),
            resume_structure_id=evidence.resume_structure_id,
            skill_name=evidence.skill_name,
            evidence_snippet=evidence.evidence_snippet,
            source_section=evidence.source_section,
            proficiency=evidence.proficiency,
        )
        self.skill_evidence.append(persisted)
        return persisted

    async def append_experience_evidence(
        self,
        evidence: ExperienceEvidence,
    ) -> ExperienceEvidence:
        persisted = ExperienceEvidence(
            id=70 + len(self.experience_evidence),
            resume_structure_id=evidence.resume_structure_id,
            role_title=evidence.role_title,
            company_redacted=evidence.company_redacted,
            duration_months=evidence.duration_months,
            evidence_snippet=evidence.evidence_snippet,
        )
        self.experience_evidence.append(persisted)
        return persisted

    async def append_education_evidence(
        self,
        evidence: EducationEvidence,
    ) -> EducationEvidence:
        persisted = EducationEvidence(
            id=80 + len(self.education_evidence),
            resume_structure_id=evidence.resume_structure_id,
            degree=evidence.degree,
            major=evidence.major,
            school_tier=evidence.school_tier,
            graduation_year=evidence.graduation_year,
            evidence_snippet=evidence.evidence_snippet,
        )
        self.education_evidence.append(persisted)
        return persisted

    async def get_max_resume_version(self, material_id: int) -> int:
        matching = [r for r in self.resume_structures if r.material_id == material_id]
        if not matching:
            return 0
        return max(r.version for r in matching)

    async def create_jd_structure(self, structure: JDStructure) -> JDStructure:
        persisted = JDStructure(
            id=90 + len(self.jd_structures),
            task_id=structure.task_id,
            material_id=structure.material_id,
            version=structure.version,
            job_title=structure.job_title,
            summary=structure.summary,
            raw_structured=structure.raw_structured,
        )
        self.jd_structures.append(persisted)
        return persisted

    async def get_latest_jd_structure_for_material(
        self,
        *,
        material_id: int,
    ) -> JDStructure | None:
        matching = [j for j in self.jd_structures if j.material_id == material_id]
        if not matching:
            return None
        return max(matching, key=lambda j: (j.version, j.id or 0))

    async def append_jd_requirement(self, requirement: JDRequirement) -> JDRequirement:
        persisted = JDRequirement(
            id=100 + len(self.jd_requirements),
            jd_structure_id=requirement.jd_structure_id,
            requirement_type=requirement.requirement_type,
            category=requirement.category,
            text=requirement.text,
            weight_hint=requirement.weight_hint,
        )
        self.jd_requirements.append(persisted)
        return persisted

    async def get_max_jd_version(self, material_id: int) -> int:
        matching = [j for j in self.jd_structures if j.material_id == material_id]
        if not matching:
            return 0
        return max(j.version for j in matching)

    async def create_match_result(self, result: MatchResult) -> MatchResult:
        persisted = MatchResult(
            id=110 + len(self.match_results),
            task_id=result.task_id,
            resume_structure_id=result.resume_structure_id,
            jd_structure_id=result.jd_structure_id,
            tier=result.tier,
            prompt_version=result.prompt_version,
            rule_version=result.rule_version,
            skill_score=result.skill_score,
            experience_score=result.experience_score,
            education_score=result.education_score,
            soft_skill_score=result.soft_skill_score,
            overall_score=result.overall_score,
        )
        self.match_results.append(persisted)
        return persisted

    async def get_match_result_for_pair(
        self,
        *,
        resume_structure_id: int,
        jd_structure_id: int,
    ) -> MatchResult | None:
        for mr in self.match_results:
            if (
                mr.resume_structure_id == resume_structure_id
                and mr.jd_structure_id == jd_structure_id
            ):
                return mr
        return None

    async def append_match_item(self, item: MatchItem) -> MatchItem:
        persisted = MatchItem(
            id=120 + len(self.match_items),
            match_result_id=item.match_result_id,
            requirement=item.requirement,
            match_status=item.match_status,
            evidence_snippet=item.evidence_snippet,
            skill_category=item.skill_category,
        )
        self.match_items.append(persisted)
        return persisted

    async def append_gap_analysis(self, gap: GapAnalysis) -> GapAnalysis:
        persisted = GapAnalysis(
            id=130 + len(self.gap_analyses),
            match_result_id=gap.match_result_id,
            gap_description=gap.gap_description,
            suggested_question=gap.suggested_question,
        )
        self.gap_analyses.append(persisted)
        return persisted

    async def append_interview_question(
        self,
        question: InterviewQuestion,
    ) -> InterviewQuestion:
        persisted = InterviewQuestion(
            id=140 + len(self.interview_questions),
            match_result_id=question.match_result_id,
            question_text=question.question_text,
            category=question.category,
            difficulty=question.difficulty,
        )
        self.interview_questions.append(persisted)
        return persisted

    async def create_report(self, report: Report) -> Report:
        persisted = Report(
            id=150 + len(self.reports),
            public_id=report.public_id,
            task_id=report.task_id,
            match_result_id=report.match_result_id,
            content_markdown=report.content_markdown,
            pdf_path=report.pdf_path,
            created_by=report.created_by,
            expires_at=report.expires_at,
        )
        self.reports.append(persisted)
        return persisted

    async def get_report_for_task(
        self,
        *,
        task_id: int,
    ) -> Report | None:
        matching = [r for r in self.reports if r.task_id == task_id]
        if not matching:
            return None
        return max(matching, key=lambda r: (r.expires_at, r.id or 0))

    async def append_manual_override(
        self,
        override: ManualOverride,
    ) -> ManualOverride:
        persisted = ManualOverride(
            id=160 + len(self.manual_overrides),
            match_result_id=override.match_result_id,
            field_path=override.field_path,
            old_value=override.old_value,
            new_value=override.new_value,
            reason=override.reason,
            admin_id=override.admin_id,
        )
        self.manual_overrides.append(persisted)
        return persisted

    async def create_prompt_version(self, prompt: PromptVersion) -> PromptVersion:
        persisted = PromptVersion(
            id=170 + len(self.prompt_versions),
            public_id=prompt.public_id,
            prompt_name=prompt.prompt_name,
            version=prompt.version,
            template_key=prompt.template_key,
            variables=prompt.variables,
            output_schema=prompt.output_schema,
            status=prompt.status,
            created_by=prompt.created_by,
        )
        self.prompt_versions.append(persisted)
        return persisted

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        for pv in self.prompt_versions:
            if pv.prompt_name == prompt_name and pv.version == version:
                return pv
        return None

    async def get_active_prompt_version(
        self,
        *,
        prompt_name: str,
    ) -> PromptVersion | None:
        matching = [
            pv
            for pv in self.prompt_versions
            if pv.prompt_name == prompt_name and pv.status is PromptStatus.ACTIVE
        ]
        if not matching:
            return None
        return max(matching, key=lambda pv: pv.id or 0)


@pytest.fixture
def service() -> RecruitDataService:
    return RecruitDataService(FakeRecruitDataRepository())


async def test_sync_user_mirror_creates_user_and_returns_with_id(
    service: RecruitDataService,
) -> None:
    user = await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name="Alice",
        role=UserRole.USER,
    )

    assert user.id == 1
    assert user.email == "alice@example.com"
    assert user.role is UserRole.USER
    assert user.status is UserStatus.ACTIVE


async def test_get_user_mirror_raises_when_missing(service: RecruitDataService) -> None:
    with pytest.raises(RecruitDataNotFoundError):
        await service.get_user_mirror("ghost")


async def test_create_task_requires_existing_user(service: RecruitDataService) -> None:
    with pytest.raises(RecruitDataNotFoundError):
        await service.create_task(
            user_public_id="ghost",
            title="Java 后端岗位 - 张三",
        )


async def test_create_task_returns_default_status_and_pending_review(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )

    task = await service.create_task(
        user_public_id="user-public-1",
        title="Java 后端岗位 - 张三",
        priority=TaskPriority.URGENT,
    )

    assert task.id == 10
    assert task.user_id == 1
    assert task.status is TaskStatus.UPLOADED
    assert task.priority is TaskPriority.URGENT
    assert task.review_status is ReviewStatus.PENDING
    assert task.reviewed_by is None
    assert task.reviewed_at is None


async def test_get_task_for_user_blocks_cross_user_access(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    await service.create_task(user_public_id="user-public-1", title=None)

    # A different requester should not see the first user's task.
    with pytest.raises(RecruitDataNotFoundError):
        await service.get_task_for_user(
            user_public_id="user-public-2",
            task_public_id="never-mind",
        )


async def test_register_material_validates_sha256(service: RecruitDataService) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    await service.create_task(user_public_id="user-public-1", title=None)

    with pytest.raises(ValueError):
        await service.register_material(
            user_public_id="user-public-1",
            task_public_id="task-does-not-matter",
            kind=MaterialKind.RESUME,
            original_filename="resume.pdf",
            file_hash="not-a-sha256",
            file_size=1024,
            mime_type="application/pdf",
        )


async def test_register_material_rejects_empty_filename_or_mime(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)

    with pytest.raises(ValueError):
        await service.register_material(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            kind=MaterialKind.RESUME,
            original_filename="",
            file_hash=VALID_SHA256_A,
            file_size=10,
            mime_type="application/pdf",
        )

    with pytest.raises(ValueError):
        await service.register_material(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            kind=MaterialKind.JD,
            original_filename="jd.pdf",
            file_hash=VALID_SHA256_A,
            file_size=10,
            mime_type="",
        )


async def test_register_material_normalizes_hash_to_lowercase_and_pending_scan(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)

    material = await service.register_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        kind=MaterialKind.RESUME,
        original_filename="resume.pdf",
        file_hash=VALID_SHA256_A.upper(),
        file_size=2048,
        mime_type="application/pdf",
    )

    assert material.task_id == task.id
    assert material.file_hash == VALID_SHA256_A  # lowercased
    assert material.scan_status is ScanStatus.PENDING
    assert material.original_deleted is False
    assert material.deleted_at is None


async def test_get_material_for_task_scopes_to_user_task(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)

    material = await service.register_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        kind=MaterialKind.JD,
        original_filename="jd.pdf",
        file_hash=VALID_SHA256_A,
        file_size=10,
        mime_type="application/pdf",
    )

    fetched = await service.get_material_for_task(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
    )
    assert fetched.id == material.id

    with pytest.raises(RecruitDataNotFoundError):
        await service.get_material_for_task(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            material_public_id="ghost",
        )


async def test_create_agent_run_creates_pending_audit_for_task(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)

    started_at = datetime(2026, 7, 5, 12, 0, 0)
    run = await service.create_agent_run(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        workflow_version="v1",
        prompt_version="v1",
        started_at=started_at,
    )

    assert run.thread_id == task.public_id
    assert run.user_id == task.user_id
    assert run.status is RunStatus.PENDING
    assert run.retry_count == 0
    assert run.error_code is None
    assert run.started_at == started_at
    assert run.finished_at is None


async def test_create_node_run_appends_to_existing_run(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)
    run = await service.create_agent_run(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        workflow_version="v1",
        prompt_version="v1",
        started_at=datetime(2026, 7, 5, 12, 0, 0),
    )

    started_at = datetime(2026, 7, 5, 12, 0, 1)
    finished_at = datetime(2026, 7, 5, 12, 0, 2)
    node_run = await service.create_node_run(
        run_id=run.id or 0,
        node_name="resume_parse",
        status=RunStatus.SUCCESS,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=1000,
        error_code=None,
        metadata={"tier": "match"},
    )

    assert node_run.run_id == run.id
    assert node_run.node_name == "resume_parse"
    assert node_run.status is RunStatus.SUCCESS
    assert node_run.metadata == {"tier": "match"}


async def test_register_material_rejects_negative_size(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)

    with pytest.raises(ValueError):
        await service.register_material(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            kind=MaterialKind.RESUME,
            original_filename="resume.pdf",
            file_hash=VALID_SHA256_B,
            file_size=-1,
            mime_type="application/pdf",
        )


async def _bootstrap_resume_owner(
    service: RecruitDataService,
    *,
    user_public_id: str = "user-public-1",
    email: str = "alice@example.com",
) -> tuple[RecruitTask, Material]:
    await service.sync_user_mirror(
        public_id=user_public_id,
        email=email,
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id=user_public_id, title=None)
    material = await service.register_material(
        user_public_id=user_public_id,
        task_public_id=task.public_id,
        kind=MaterialKind.RESUME,
        original_filename="resume.pdf",
        file_hash=VALID_SHA256_A,
        file_size=2048,
        mime_type="application/pdf",
    )
    return task, material


async def test_create_resume_structure_increments_version(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)

    raw_structured: dict[str, Any] = {
        "skills": [{"name": "Python"}],
        "experiences": [],
        "educations": [],
    }
    first = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary="Backend engineer with Python experience",
        total_years_exp=5.0,
        raw_structured=raw_structured,
    )
    second = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary="Updated summary after reparse",
        total_years_exp=6.0,
        raw_structured=raw_structured,
    )

    assert first.version == 1
    assert first.task_id == task.id == 10
    assert first.material_id == material.id
    assert second.version == 2

    latest = await service.get_latest_resume_structure_for_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
    )
    assert latest is not None
    assert latest.version == 2
    assert latest.summary == "Updated summary after reparse"


async def test_create_resume_structure_rejects_jd_material(
    service: RecruitDataService,
) -> None:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)
    jd_material = await service.register_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        kind=MaterialKind.JD,
        original_filename="jd.pdf",
        file_hash=VALID_SHA256_A,
        file_size=1024,
        mime_type="application/pdf",
    )

    with pytest.raises(ValueError):
        await service.create_resume_structure(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            material_public_id=jd_material.public_id,
            summary=None,
            total_years_exp=None,
            raw_structured={"skills": []},
        )


async def test_create_resume_structure_rejects_cross_user_access(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)

    with pytest.raises(RecruitDataNotFoundError):
        await service.create_resume_structure(
            user_public_id="user-public-2",
            task_public_id=task.public_id,
            material_public_id=material.public_id,
            summary=None,
            total_years_exp=None,
            raw_structured={},
        )


async def test_create_resume_structure_rejects_negative_years_exp(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)

    with pytest.raises(ValueError):
        await service.create_resume_structure(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            material_public_id=material.public_id,
            summary=None,
            total_years_exp=-0.5,
            raw_structured={},
        )


async def test_append_skill_evidence_persists_with_proficiency(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)
    structure = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary=None,
        total_years_exp=None,
        raw_structured={},
    )

    skill = await service.append_skill_evidence(
        resume_structure=structure,
        skill_name="Python",
        evidence_snippet="3 years building FastAPI services",
        source_section="skills",
        proficiency=Proficiency.ADVANCED,
    )

    assert skill.id is not None
    assert skill.resume_structure_id == structure.id
    assert skill.skill_name == "Python"
    assert skill.proficiency is Proficiency.ADVANCED


async def test_append_skill_evidence_rejects_empty_snippet(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)
    structure = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary=None,
        total_years_exp=None,
        raw_structured={},
    )

    with pytest.raises(ValueError):
        await service.append_skill_evidence(
            resume_structure=structure,
            skill_name="Python",
            evidence_snippet="",
        )


async def test_append_experience_evidence_persists_redacted_company(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)
    structure = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary=None,
        total_years_exp=None,
        raw_structured={},
    )

    exp = await service.append_experience_evidence(
        resume_structure=structure,
        role_title="Backend Engineer",
        evidence_snippet="Built order service handling 10k QPS",
        company_redacted="Company-A",
        duration_months=24,
    )

    assert exp.role_title == "Backend Engineer"
    assert exp.duration_months == 24
    assert exp.company_redacted == "Company-A"


async def test_append_experience_evidence_rejects_negative_duration(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)
    structure = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary=None,
        total_years_exp=None,
        raw_structured={},
    )

    with pytest.raises(ValueError):
        await service.append_experience_evidence(
            resume_structure=structure,
            role_title="Backend Engineer",
            evidence_snippet="snippet",
            duration_months=-1,
        )


async def test_append_education_evidence_persists_degree_and_tier(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)
    structure = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary=None,
        total_years_exp=None,
        raw_structured={},
    )

    edu = await service.append_education_evidence(
        resume_structure=structure,
        evidence_snippet="B.Sc. Computer Science, 2020",
        degree=Degree.BACHELOR,
        major="Computer Science",
        school_tier=SchoolTier.TIER1,
        graduation_year=2020,
    )

    assert edu.degree is Degree.BACHELOR
    assert edu.school_tier is SchoolTier.TIER1
    assert edu.graduation_year == 2020


async def test_append_education_evidence_rejects_year_before_1900(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_resume_owner(service)
    structure = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        summary=None,
        total_years_exp=None,
        raw_structured={},
    )

    with pytest.raises(ValueError):
        await service.append_education_evidence(
            resume_structure=structure,
            evidence_snippet="graduated",
            graduation_year=1899,
        )


async def _bootstrap_jd_owner(
    service: RecruitDataService,
) -> tuple[RecruitTask, Material]:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)
    material = await service.register_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        kind=MaterialKind.JD,
        original_filename="jd.pdf",
        file_hash=VALID_SHA256_A,
        file_size=1024,
        mime_type="application/pdf",
    )
    return task, material


async def test_create_jd_structure_increments_version(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_jd_owner(service)

    first = await service.create_jd_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        job_title="Backend Engineer",
        summary="Build order services",
        raw_structured={"requirements": []},
    )
    second = await service.create_jd_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        job_title="Backend Engineer (revised)",
        summary=None,
        raw_structured={"requirements": []},
    )

    assert first.version == 1
    assert first.job_title == "Backend Engineer"
    assert second.version == 2

    latest = await service.get_latest_jd_structure_for_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
    )
    assert latest is not None
    assert latest.version == 2
    assert latest.job_title == "Backend Engineer (revised)"


async def test_create_jd_structure_rejects_resume_material(
    service: RecruitDataService,
) -> None:
    task, _resume_material = await _bootstrap_resume_owner(service)
    # Reuse the same task but try to attach a JD structure to a resume material
    # by registering a resume-typed material then attempting JD create.
    resume_material = await service.register_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        kind=MaterialKind.RESUME,
        original_filename="resume2.pdf",
        file_hash=VALID_SHA256_B,
        file_size=2048,
        mime_type="application/pdf",
    )

    with pytest.raises(ValueError):
        await service.create_jd_structure(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            material_public_id=resume_material.public_id,
            job_title=None,
            summary=None,
            raw_structured={},
        )


async def test_append_jd_requirement_persists_with_weight_hint(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_jd_owner(service)
    structure = await service.create_jd_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        job_title=None,
        summary=None,
        raw_structured={},
    )

    req_must = await service.append_jd_requirement(
        jd_structure=structure,
        requirement_type=RequirementType.MUST_HAVE,
        text="3+ years Python",
        category="skill",
        weight_hint=0.9,
    )
    req_nice = await service.append_jd_requirement(
        jd_structure=structure,
        requirement_type=RequirementType.NICE_TO_HAVE,
        text="Kafka experience",
        category="skill",
        weight_hint=None,
    )

    assert req_must.requirement_type is RequirementType.MUST_HAVE
    assert req_must.weight_hint == 0.9
    assert req_nice.requirement_type is RequirementType.NICE_TO_HAVE
    assert req_nice.weight_hint is None


async def test_append_jd_requirement_rejects_empty_text(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_jd_owner(service)
    structure = await service.create_jd_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        job_title=None,
        summary=None,
        raw_structured={},
    )

    with pytest.raises(ValueError):
        await service.append_jd_requirement(
            jd_structure=structure,
            requirement_type=RequirementType.MUST_HAVE,
            text="",
        )


async def test_append_jd_requirement_rejects_out_of_range_weight(
    service: RecruitDataService,
) -> None:
    task, material = await _bootstrap_jd_owner(service)
    structure = await service.create_jd_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=material.public_id,
        job_title=None,
        summary=None,
        raw_structured={},
    )

    with pytest.raises(ValueError):
        await service.append_jd_requirement(
            jd_structure=structure,
            requirement_type=RequirementType.NICE_TO_HAVE,
            text="something",
            weight_hint=1.5,
        )

    with pytest.raises(ValueError):
        await service.append_jd_requirement(
            jd_structure=structure,
            requirement_type=RequirementType.NICE_TO_HAVE,
            text="something",
            weight_hint=-0.1,
        )


async def _bootstrap_match_owner(
    service: RecruitDataService,
) -> tuple[RecruitTask, ResumeStructure, JDStructure]:
    await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )
    task = await service.create_task(user_public_id="user-public-1", title=None)
    resume_material = await service.register_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        kind=MaterialKind.RESUME,
        original_filename="resume.pdf",
        file_hash=VALID_SHA256_A,
        file_size=2048,
        mime_type="application/pdf",
    )
    jd_material = await service.register_material(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        kind=MaterialKind.JD,
        original_filename="jd.pdf",
        file_hash=VALID_SHA256_B,
        file_size=1024,
        mime_type="application/pdf",
    )
    resume_structure = await service.create_resume_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=resume_material.public_id,
        summary=None,
        total_years_exp=None,
        raw_structured={},
    )
    jd_structure = await service.create_jd_structure(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        material_public_id=jd_material.public_id,
        job_title=None,
        summary=None,
        raw_structured={},
    )
    return task, resume_structure, jd_structure


async def test_create_match_result_persists_with_required_versions(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)

    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
        skill_score=85.0,
        experience_score=80.0,
        education_score=90.0,
        soft_skill_score=70.0,
        overall_score=82.5,
    )

    assert match.id is not None
    assert match.tier is MatchTier.MATCH
    assert match.rule_version == "rules-v1"
    assert match.overall_score == 82.5


async def test_create_match_result_rejects_empty_rule_version(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)

    with pytest.raises(ValueError):
        await service.create_match_result(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            resume_structure=resume_structure,
            jd_structure=jd_structure,
            tier=MatchTier.PARTIAL,
            prompt_version="v1",
            rule_version="",
        )


async def test_create_match_result_rejects_duplicate_pair(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)

    await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.PARTIAL,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.create_match_result(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            resume_structure=resume_structure,
            jd_structure=jd_structure,
            tier=MatchTier.MATCH,
            prompt_version="v1",
            rule_version="rules-v1",
        )


async def test_create_match_result_rejects_score_out_of_range(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)

    with pytest.raises(ValueError):
        await service.create_match_result(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            resume_structure=resume_structure,
            jd_structure=jd_structure,
            tier=MatchTier.MATCH,
            prompt_version="v1",
            rule_version="rules-v1",
            overall_score=120.0,
        )


async def test_append_match_item_blocks_evidence_on_no_evidence(
    service: RecruitDataService,
) -> None:
    """ADR-0009 invariant: no-evidence items must not be filled with ability."""
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.NO_EVIDENCE,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.append_match_item(
            match_result=match,
            requirement="Kafka",
            match_status=MatchTier.NO_EVIDENCE,
            evidence_snippet="workshop",
            skill_category=SkillCategory.SKILL,
        )


async def test_append_match_item_persists_with_evidence(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    item = await service.append_match_item(
        match_result=match,
        requirement="3+ years Python",
        match_status=MatchTier.MATCH,
        evidence_snippet="5 years building FastAPI services",
        skill_category=SkillCategory.SKILL,
    )

    assert item.match_status is MatchTier.MATCH
    assert item.skill_category is SkillCategory.SKILL


async def test_append_gap_analysis_persists_with_seed_question(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.PARTIAL,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    gap = await service.append_gap_analysis(
        match_result=match,
        gap_description="Resume lacks Kafka streaming experience",
        suggested_question="Describe a Kafka consumer group you have operated.",
    )

    assert gap.id is not None
    assert gap.match_result_id == match.id
    assert gap.suggested_question is not None


async def test_append_gap_analysis_rejects_empty_description(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.PARTIAL,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.append_gap_analysis(
            match_result=match,
            gap_description="",
            suggested_question=None,
        )


async def test_append_interview_question_persists_with_category_and_difficulty(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    q = await service.append_interview_question(
        match_result=match,
        question_text="Walk me through a Python GIL bottleneck you debugged.",
        category=QuestionCategory.SKILL_VERIFICATION,
        difficulty=QuestionDifficulty.HARD,
    )

    assert q.id is not None
    assert q.match_result_id == match.id
    assert q.category is QuestionCategory.SKILL_VERIFICATION
    assert q.difficulty is QuestionDifficulty.HARD


async def test_append_interview_question_allows_optional_difficulty(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    q = await service.append_interview_question(
        match_result=match,
        question_text="Tell me about a time you led a migration.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=None,
    )

    assert q.difficulty is None
    assert q.category is QuestionCategory.BEHAVIORAL


async def test_append_interview_question_rejects_empty_text(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.append_interview_question(
            match_result=match,
            question_text="",
            category=QuestionCategory.GAP_PROBE,
        )


async def test_create_report_persists_with_expiry(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    expires_at = datetime.now() + timedelta(days=30)
    report = await service.create_report(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        match_result=match,
        content_markdown="# 招聘分析报告\n\n结论：建议进入面试。",
        created_by=1,
        expires_at=expires_at,
        pdf_path=None,
    )

    assert report.id is not None
    assert report.task_id == task.id
    assert report.match_result_id == match.id
    assert report.created_by == 1
    assert report.expires_at == expires_at
    assert report.pdf_path is None


async def test_create_report_rejects_empty_content(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.create_report(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            match_result=match,
            content_markdown="",
            created_by=1,
            expires_at=datetime.now() + timedelta(days=1),
        )


async def test_create_report_rejects_past_expiry(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.create_report(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            match_result=match,
            content_markdown="# Report",
            created_by=1,
            expires_at=datetime.now() - timedelta(seconds=1),
        )


async def test_create_report_rejects_invalid_creator(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.create_report(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            match_result=match,
            content_markdown="# Report",
            created_by=0,
            expires_at=datetime.now() + timedelta(days=1),
        )


async def test_create_report_rejects_match_from_other_task(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    # Construct a MatchResult entity that claims to belong to a different task.
    foreign_match = MatchResult(
        id=999,
        task_id=888,
        resume_structure_id=resume_structure.id or 0,
        jd_structure_id=jd_structure.id or 0,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(RecruitDataNotFoundError):
        await service.create_report(
            user_public_id="user-public-1",
            task_public_id=task.public_id,
            match_result=foreign_match,
            content_markdown="# Stolen report",
            created_by=1,
            expires_at=datetime.now() + timedelta(days=1),
        )


async def test_get_report_for_task_returns_latest(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    await service.create_report(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        match_result=match,
        content_markdown="v1",
        created_by=1,
        expires_at=datetime.now() + timedelta(days=1),
    )
    await service.create_report(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        match_result=match,
        content_markdown="v2",
        created_by=1,
        expires_at=datetime.now() + timedelta(days=30),
    )

    fetched = await service.get_report_for_task(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
    )
    assert fetched is not None
    assert fetched.content_markdown == "v2"


async def test_append_manual_override_persists_audit_row(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.PARTIAL,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    override = await service.append_manual_override(
        match_result=match,
        field_path="match_items[2].match_status",
        old_value="partial",
        new_value="match",
        reason="候选人补交 Kafka 项目代码后再次评估，证据已足够。",
        admin_id=1,
    )

    assert override.id is not None
    assert override.match_result_id == match.id
    assert override.admin_id == 1
    assert override.field_path == "match_items[2].match_status"


async def test_append_manual_override_rejects_empty_reason(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.append_manual_override(
            match_result=match,
            field_path="tier",
            old_value="partial",
            new_value="match",
            reason="",
            admin_id=1,
        )


async def test_append_manual_override_rejects_empty_field_path(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.append_manual_override(
            match_result=match,
            field_path="",
            reason="合法理由",
            admin_id=1,
        )


async def test_append_manual_override_rejects_invalid_admin(
    service: RecruitDataService,
) -> None:
    task, resume_structure, jd_structure = await _bootstrap_match_owner(service)
    match = await service.create_match_result(
        user_public_id="user-public-1",
        task_public_id=task.public_id,
        resume_structure=resume_structure,
        jd_structure=jd_structure,
        tier=MatchTier.MATCH,
        prompt_version="v1",
        rule_version="rules-v1",
    )

    with pytest.raises(ValueError):
        await service.append_manual_override(
            match_result=match,
            field_path="tier",
            reason="合法理由",
            admin_id=0,
        )


async def _bootstrap_admin(service: RecruitDataService) -> UserMirror:
    return await service.sync_user_mirror(
        public_id="admin-public-1",
        email="admin@example.com",
        display_name="HR Admin",
        role=UserRole.ADMIN,
    )


async def test_create_prompt_version_persists_with_draft_status(
    service: RecruitDataService,
) -> None:
    admin = await _bootstrap_admin(service)

    prompt = await service.create_prompt_version(
        creator=admin,
        prompt_name="recruit_resume_parse",
        version="v3",
        template_key="recruit_resume_parse/v3",
        variables={"required": ["resume_text"]},
        output_schema={"type": "object"},
    )

    assert prompt.id is not None
    assert prompt.status is PromptStatus.DRAFT
    assert prompt.created_by == admin.id
    assert prompt.variables == {"required": ["resume_text"]}


async def test_create_prompt_version_rejects_non_admin_creator(
    service: RecruitDataService,
) -> None:
    user = await service.sync_user_mirror(
        public_id="user-public-1",
        email="alice@example.com",
        display_name=None,
        role=UserRole.USER,
    )

    with pytest.raises(ForbiddenError):
        await service.create_prompt_version(
            creator=user,
            prompt_name="recruit_resume_parse",
            version="v1",
            template_key="recruit_resume_parse/v1",
        )


async def test_create_prompt_version_rejects_unsafe_template_keys(
    service: RecruitDataService,
) -> None:
    admin = await _bootstrap_admin(service)

    bad_keys = (
        "",
        "/absolute/path",
        "../escape",
        "recruit_resume_parse/../escape",
        "recruit\\resume_parse",
        "C:/windows/drive",
        "recruit_resume_parse//v1",
    )

    for bad in bad_keys:
        with pytest.raises(ValueError, match="template_key"):
            await service.create_prompt_version(
                creator=admin,
                prompt_name="recruit_resume_parse",
                version="v-x",
                template_key=bad,
            )


async def test_create_prompt_version_rejects_duplicate_pair(
    service: RecruitDataService,
) -> None:
    admin = await _bootstrap_admin(service)

    await service.create_prompt_version(
        creator=admin,
        prompt_name="recruit_resume_parse",
        version="v1",
        template_key="recruit_resume_parse/v1",
    )

    with pytest.raises(ValueError, match="already exists"):
        await service.create_prompt_version(
            creator=admin,
            prompt_name="recruit_resume_parse",
            version="v1",
            template_key="recruit_resume_parse/v1-bis",
        )


async def test_create_prompt_version_rejects_empty_name_or_version(
    service: RecruitDataService,
) -> None:
    admin = await _bootstrap_admin(service)

    with pytest.raises(ValueError):
        await service.create_prompt_version(
            creator=admin,
            prompt_name="",
            version="v1",
            template_key="recruit_resume_parse/v1",
        )

    with pytest.raises(ValueError):
        await service.create_prompt_version(
            creator=admin,
            prompt_name="recruit_resume_parse",
            version="",
            template_key="recruit_resume_parse/v1",
        )


async def test_get_prompt_version_returns_persisted_row(
    service: RecruitDataService,
) -> None:
    admin = await _bootstrap_admin(service)
    await service.create_prompt_version(
        creator=admin,
        prompt_name="recruit_evidence_match",
        version="v2",
        template_key="recruit_evidence_match/v2",
    )

    fetched = await service.get_prompt_version(
        prompt_name="recruit_evidence_match",
        version="v2",
    )
    assert fetched is not None
    assert fetched.template_key == "recruit_evidence_match/v2"


async def test_get_active_prompt_version_returns_none_without_active(
    service: RecruitDataService,
) -> None:
    admin = await _bootstrap_admin(service)
    await service.create_prompt_version(
        creator=admin,
        prompt_name="recruit_evidence_match",
        version="v1",
        template_key="recruit_evidence_match/v1",
    )

    fetched = await service.get_active_prompt_version(
        prompt_name="recruit_evidence_match",
    )
    assert fetched is None
