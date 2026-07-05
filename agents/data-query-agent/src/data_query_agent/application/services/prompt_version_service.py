"""Application service for prompt version management."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from data_query_agent.domain.entities.identity import UserMirror, UserRole
from data_query_agent.domain.entities.prompt_version import PromptVersion
from data_query_agent.domain.ports.prompt_version_repository import PromptVersionRepository


class PromptVersionService:
    """Use cases for admin-managed prompt versions."""

    def __init__(self, repository: PromptVersionRepository) -> None:
        self._repository = repository

    async def create_prompt_version(
        self,
        *,
        admin_user: UserMirror,
        prompt_name: str,
        version: str,
        template_hash: str,
        template_body: str,
        variables_schema: str,
        output_schema: str,
        is_active: bool = False,
    ) -> PromptVersion:
        """Create a prompt version only when the caller is an admin mirror."""
        if admin_user.id is None:
            raise ValueError("persisted user mirror must have an id")
        if admin_user.role is not UserRole.ADMIN:
            raise PermissionError("admin role required for prompt version creation")
        existing = await self._repository.get_prompt_version(
            prompt_name=prompt_name,
            version=version,
        )
        if existing is not None:
            raise ValueError("prompt version already exists")
        return await self._repository.create_prompt_version(
            public_id=str(uuid4()),
            prompt_name=prompt_name,
            version=version,
            template_hash=template_hash,
            template_body=template_body,
            variables_schema=variables_schema,
            output_schema=output_schema,
            is_active=is_active,
            created_by_user_id=admin_user.id,
        )

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        """Get a specific prompt version for workflow references."""
        return await self._repository.get_prompt_version(
            prompt_name=prompt_name,
            version=version,
        )

    async def list_prompt_versions(
        self,
        *,
        prompt_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[PromptVersion]:
        """List prompt versions for admin review or deterministic selection."""
        return await self._repository.list_prompt_versions(
            prompt_name=prompt_name,
            limit=limit,
            offset=offset,
        )
