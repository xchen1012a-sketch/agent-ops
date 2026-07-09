"""ORM model exports.

Importing this package registers all model tables on ``Base.metadata`` for
Alembic autogenerate.
"""

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

__all__ = [
    "AgentRunModel",
    "EducationEvidenceModel",
    "ExperienceEvidenceModel",
    "GapAnalysisModel",
    "InterviewQuestionModel",
    "JDRequirementModel",
    "JDStructureModel",
    "ManualOverrideModel",
    "MatchItemModel",
    "MatchResultModel",
    "MaterialModel",
    "NodeRunModel",
    "PromptVersionModel",
    "RecruitTaskModel",
    "ReportModel",
    "ResumeStructureModel",
    "SkillEvidenceModel",
    "UserModel",
]
