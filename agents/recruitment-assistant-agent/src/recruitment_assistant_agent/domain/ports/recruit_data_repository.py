"""Repository port for RECRUIT-230 identity and data persistence."""

from __future__ import annotations

from typing import Protocol

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


class RecruitDataRepository(Protocol):
    """Persistence contract used by application services.

    Implementations must not commit transactions; callers own transaction
    boundaries through the active SQLAlchemy session.
    """

    async def upsert_user_mirror(self, user: UserMirror) -> UserMirror:
        """Create or update a user mirror by public ID."""

    async def get_user_by_public_id(self, public_id: str) -> UserMirror | None:
        """Return a user mirror by public ID."""

    async def create_task(self, task: RecruitTask) -> RecruitTask:
        """Persist a recruitment analysis task."""

    async def get_task_for_user(
        self,
        *,
        task_public_id: str,
        user_id: int,
    ) -> RecruitTask | None:
        """Return a user-owned task or None when absent/unauthorized."""

    async def register_material(self, material: Material) -> Material:
        """Persist metadata for an uploaded resume or JD material."""

    async def get_material_for_task(
        self,
        *,
        material_public_id: str,
        task_id: int,
    ) -> Material | None:
        """Return a material belonging to a task, or None."""

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        """Persist an Agent run audit record."""

    async def update_agent_run(self, run: AgentRun) -> AgentRun:
        """Update an existing Agent run audit record."""

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        """Persist an Agent node audit record."""

    async def update_node_run(self, node_run: NodeRun) -> NodeRun:
        """Update an existing Agent node audit record."""

    async def create_resume_structure(self, structure: ResumeStructure) -> ResumeStructure:
        """Persist a new resume structure version for a task's material."""

    async def get_latest_resume_structure_for_material(
        self,
        *,
        material_id: int,
    ) -> ResumeStructure | None:
        """Return the highest-version resume structure for a material, or None."""

    async def get_resume_structure(
        self,
        *,
        resume_structure_id: int,
    ) -> ResumeStructure | None:
        """Return a resume structure by id, or None."""

    async def append_skill_evidence(self, evidence: SkillEvidence) -> SkillEvidence:
        """Append a skill evidence row tied to a resume structure."""

    async def append_experience_evidence(
        self,
        evidence: ExperienceEvidence,
    ) -> ExperienceEvidence:
        """Append a work experience evidence row tied to a resume structure."""

    async def append_education_evidence(
        self,
        evidence: EducationEvidence,
    ) -> EducationEvidence:
        """Append an education evidence row tied to a resume structure."""

    async def get_max_resume_version(self, material_id: int) -> int:
        """Return the max resume version for a material, or 0 if none exists."""

    async def create_jd_structure(self, structure: JDStructure) -> JDStructure:
        """Persist a new JD structure version for a task's material."""

    async def get_latest_jd_structure_for_material(
        self,
        *,
        material_id: int,
    ) -> JDStructure | None:
        """Return the highest-version JD structure for a material, or None."""

    async def append_jd_requirement(self, requirement: JDRequirement) -> JDRequirement:
        """Append a JD requirement row to an existing JD structure."""

    async def get_max_jd_version(self, material_id: int) -> int:
        """Return the max JD version for a material, or 0 if none exists."""

    async def create_match_result(self, result: MatchResult) -> MatchResult:
        """Persist a match result for a resume/JD structure pair."""

    async def get_match_result_for_pair(
        self,
        *,
        resume_structure_id: int,
        jd_structure_id: int,
    ) -> MatchResult | None:
        """Return an existing match result for a resume/JD pair, or None."""

    async def append_match_item(self, item: MatchItem) -> MatchItem:
        """Append a per-requirement match item to an existing match result."""

    async def append_gap_analysis(self, gap: GapAnalysis) -> GapAnalysis:
        """Append a gap analysis row tied to an existing match result."""

    async def append_interview_question(
        self,
        question: InterviewQuestion,
    ) -> InterviewQuestion:
        """Append a structured interview question to an existing match result."""

    async def create_report(self, report: Report) -> Report:
        """Persist a recruitment analysis report tied to a task and match result."""

    async def get_report_for_task(
        self,
        *,
        task_id: int,
    ) -> Report | None:
        """Return the most recently created report for a task, or None."""

    async def append_manual_override(
        self,
        override: ManualOverride,
    ) -> ManualOverride:
        """Append an admin-authored override audit row to a match result."""

    async def create_prompt_version(self, prompt: PromptVersion) -> PromptVersion:
        """Persist a new prompt version row scoped to (prompt_name, version)."""

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        """Return a prompt version by (prompt_name, version), or None."""

    async def get_active_prompt_version(
        self,
        *,
        prompt_name: str,
    ) -> PromptVersion | None:
        """Return the currently active prompt version for a name, or None."""
