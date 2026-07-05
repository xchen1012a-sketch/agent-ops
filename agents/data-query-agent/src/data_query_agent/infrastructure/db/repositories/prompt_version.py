"""SQLAlchemy repository for prompt version records."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.domain.entities.prompt_version import PromptVersion
from data_query_agent.infrastructure.db.models.prompt_version import PromptVersionModel


class SqlAlchemyPromptVersionRepository:
    """SQLAlchemy implementation of the prompt version repository port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        model = PromptVersionModel(
            public_id=public_id,
            prompt_name=prompt_name,
            version=version,
            template_hash=template_hash,
            template_body=template_body,
            variables_schema=variables_schema,
            output_schema=output_schema,
            is_active=is_active,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def get_prompt_version(
        self,
        *,
        prompt_name: str,
        version: str,
    ) -> PromptVersion | None:
        result = await self._session.execute(
            select(PromptVersionModel).where(
                PromptVersionModel.prompt_name == prompt_name,
                PromptVersionModel.version == version,
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_prompt_versions(
        self,
        *,
        prompt_name: str | None,
        limit: int,
        offset: int,
    ) -> Sequence[PromptVersion]:
        statement = select(PromptVersionModel)
        if prompt_name is not None:
            statement = statement.where(PromptVersionModel.prompt_name == prompt_name)
        result = await self._session.execute(
            statement.order_by(PromptVersionModel.created_at.desc(), PromptVersionModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return tuple(_to_entity(model) for model in result.scalars().all())


def _to_entity(model: PromptVersionModel) -> PromptVersion:
    return PromptVersion(
        id=model.id,
        public_id=model.public_id,
        prompt_name=model.prompt_name,
        version=model.version,
        template_hash=model.template_hash,
        template_body=model.template_body,
        variables_schema=model.variables_schema,
        output_schema=model.output_schema,
        is_active=model.is_active,
        created_by_user_id=model.created_by_user_id,
        created_at=model.created_at,
    )
