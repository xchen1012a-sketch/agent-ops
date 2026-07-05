"""Repository port for prompt version records."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from data_query_agent.domain.entities.prompt_version import PromptVersion


class PromptVersionRepository(Protocol):
    """Persistence boundary for versioned prompt templates."""

    async def create_prompt_version(
        self,
        *,
        public_id: str,
        prompt_name: str,
        version: str,
        template_hash: str,
        template_body: str,
        variables_schema: str,
        output_schema: str,
        is_active: bool,
        created_by_user_id: int,
    ) -> PromptVersion:
        """Create a prompt version record."""

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        """Return a specific prompt version."""

    async def list_prompt_versions(
        self,
        *,
        prompt_name: str | None,
        limit: int,
        offset: int,
    ) -> Sequence[PromptVersion]:
        """List prompt versions for admin or workflow selection."""
