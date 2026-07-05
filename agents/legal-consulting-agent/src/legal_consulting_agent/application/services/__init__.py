"""Application service exports."""

from legal_consulting_agent.application.services.legal_data_service import (
    LegalDataNotFoundError,
    LegalDataService,
)

__all__ = ["LegalDataNotFoundError", "LegalDataService"]
