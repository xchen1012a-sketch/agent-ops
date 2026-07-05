"""Unit tests for prompt version application service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from data_query_agent.application.services.prompt_version_service import PromptVersionService
from data_query_agent.domain.entities.identity import UserMirror, UserRole
from data_query_agent.domain.entities.prompt_version import PromptVersion


class FakePromptVersionRepository:
    """In-memory prompt version repository for service tests."""

    def __init__(self) -> None:
        self.versions: list[PromptVersion] = []
        self.next_id = 1

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
        prompt_version = PromptVersion(
            id=self.next_id,
            public_id=public_id,
            prompt_name=prompt_name,
            version=version,
            template_hash=template_hash,
            template_body=template_body,
            variables_schema=variables_schema,
            output_schema=output_schema,
            is_active=is_active,
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.next_id += 1
        self.versions.append(prompt_version)
        return prompt_version

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        for prompt_version in self.versions:
            if prompt_version.prompt_name == prompt_name and prompt_version.version == version:
                return prompt_version
        return None

    async def list_prompt_versions(
        self,
        *,
        prompt_name: str | None,
        limit: int,
        offset: int,
    ) -> Sequence[PromptVersion]:
        versions = self.versions
        if prompt_name is not None:
            versions = [version for version in versions if version.prompt_name == prompt_name]
        return tuple(versions[offset : offset + limit])


def _user(*, user_id: int = 20, role: UserRole = UserRole.ADMIN) -> UserMirror:
    now = datetime.now(UTC).replace(tzinfo=None)
    return UserMirror(
        id=user_id,
        public_id=f"user-{user_id}",
        external_subject=f"subject-{user_id}",
        role=role,
        display_name=None,
        created_at=now,
        updated_at=now,
        last_seen_at=now,
    )


@pytest.mark.asyncio
async def test_admin_can_create_prompt_version() -> None:
    service = PromptVersionService(FakePromptVersionRepository())

    prompt_version = await service.create_prompt_version(
        admin_user=_user(role=UserRole.ADMIN),
        prompt_name="nl2sql",
        version="v1",
        template_hash="sha256:prompt",
        template_body="{{question}}",
        variables_schema='{"required":["question"]}',
        output_schema='{"type":"object"}',
        is_active=True,
    )

    assert prompt_version.prompt_name == "nl2sql"
    assert prompt_version.version == "v1"
    assert prompt_version.template_hash == "sha256:prompt"
    assert prompt_version.is_active is True
    assert prompt_version.created_by_user_id == 20


@pytest.mark.asyncio
async def test_non_admin_cannot_create_prompt_version() -> None:
    service = PromptVersionService(FakePromptVersionRepository())

    with pytest.raises(PermissionError):
        await service.create_prompt_version(
            admin_user=_user(role=UserRole.USER),
            prompt_name="nl2sql",
            version="v1",
            template_hash="sha256:prompt",
            template_body="{{question}}",
            variables_schema="{}",
            output_schema="{}",
        )


@pytest.mark.asyncio
async def test_duplicate_prompt_version_is_rejected() -> None:
    service = PromptVersionService(FakePromptVersionRepository())
    admin = _user(role=UserRole.ADMIN)
    await service.create_prompt_version(
        admin_user=admin,
        prompt_name="interpret_result",
        version="v1",
        template_hash="sha256:first",
        template_body="template",
        variables_schema="{}",
        output_schema="{}",
    )

    with pytest.raises(ValueError):
        await service.create_prompt_version(
            admin_user=admin,
            prompt_name="interpret_result",
            version="v1",
            template_hash="sha256:second",
            template_body="template",
            variables_schema="{}",
            output_schema="{}",
        )


@pytest.mark.asyncio
async def test_workflow_can_reference_prompt_version_by_name_and_version() -> None:
    service = PromptVersionService(FakePromptVersionRepository())
    created = await service.create_prompt_version(
        admin_user=_user(role=UserRole.ADMIN),
        prompt_name="nl2sql",
        version="v2",
        template_hash="sha256:v2",
        template_body="template",
        variables_schema="{}",
        output_schema="{}",
    )

    found = await service.get_prompt_version(prompt_name="nl2sql", version="v2")
    missing = await service.get_prompt_version(prompt_name="nl2sql", version="v3")

    assert found == created
    assert missing is None


@pytest.mark.asyncio
async def test_list_prompt_versions_can_filter_by_prompt_name() -> None:
    service = PromptVersionService(FakePromptVersionRepository())
    admin = _user(role=UserRole.ADMIN)
    first = await service.create_prompt_version(
        admin_user=admin,
        prompt_name="nl2sql",
        version="v1",
        template_hash="sha256:one",
        template_body="template",
        variables_schema="{}",
        output_schema="{}",
    )
    await service.create_prompt_version(
        admin_user=admin,
        prompt_name="interpret_result",
        version="v1",
        template_hash="sha256:two",
        template_body="template",
        variables_schema="{}",
        output_schema="{}",
    )

    versions = await service.list_prompt_versions(prompt_name="nl2sql")

    assert versions == (first,)


@pytest.mark.asyncio
async def test_rejects_unpersisted_admin_user() -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    service = PromptVersionService(FakePromptVersionRepository())
    admin = UserMirror(
        id=None,
        public_id="user-none",
        external_subject="subject-none",
        role=UserRole.ADMIN,
        display_name=None,
        created_at=now,
        updated_at=now,
        last_seen_at=now,
    )

    with pytest.raises(ValueError):
        await service.create_prompt_version(
            admin_user=admin,
            prompt_name="nl2sql",
            version="v1",
            template_hash="sha256:prompt",
            template_body="template",
            variables_schema="{}",
            output_schema="{}",
        )
