"""ORM model exports.

Importing this package registers all model tables on ``Base.metadata`` for
Alembic autogenerate.
"""

from legal_consulting_agent.infrastructure.db.models.legal_data import (
    AgentRunModel,
    ConsultationRecordModel,
    FeedbackModel,
    HighRiskReviewModel,
    KnowledgeMaterialModel,
    LegalCategoryModel,
    LegalMessageModel,
    LegalSessionModel,
    NodeRunModel,
    PromptVersionModel,
    UserModel,
)

__all__ = [
    "AgentRunModel",
    "ConsultationRecordModel",
    "FeedbackModel",
    "HighRiskReviewModel",
    "KnowledgeMaterialModel",
    "PromptVersionModel",
    "LegalCategoryModel",
    "LegalMessageModel",
    "LegalSessionModel",
    "NodeRunModel",
    "UserModel",
]
