"""Repository implementations backed by SQLAlchemy."""

from legal_consulting_agent.infrastructure.db.repositories.legal_data import (
    SqlAlchemyLegalDataRepository,
)

__all__ = ["SqlAlchemyLegalDataRepository"]
