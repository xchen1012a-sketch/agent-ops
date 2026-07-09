"""Repository implementations backed by SQLAlchemy."""

from recruitment_assistant_agent.infrastructure.db.repositories.recruit_data import (
    SqlAlchemyRecruitDataRepository,
)

__all__ = ["SqlAlchemyRecruitDataRepository"]
