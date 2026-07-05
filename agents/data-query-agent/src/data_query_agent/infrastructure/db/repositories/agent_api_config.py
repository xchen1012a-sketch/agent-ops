"""Repository for agent_api_config (CONFIG-100)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.domain.entities.agent_api_config import AgentApiConfig
from data_query_agent.infrastructure.db.models.agent_api_config import (
    AgentApiConfigModel,
)


class SqlAlchemyAgentApiConfigRepository:
    """Persist agent_api_config rows using an externally managed session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_public_id: str) -> list[AgentApiConfig]:
        result = await self._session.execute(
            select(AgentApiConfigModel)
            .where(AgentApiConfigModel.user_public_id == user_public_id)
            .order_by(AgentApiConfigModel.id.asc())
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_type(self, user_public_id: str, api_type: str) -> AgentApiConfig | None:
        result = await self._session.execute(
            select(AgentApiConfigModel).where(
                AgentApiConfigModel.user_public_id == user_public_id,
                AgentApiConfigModel.api_type == api_type,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model is not None else None

    async def upsert(
        self,
        *,
        user_public_id: str,
        api_type: str,
        display_name: str,
        base_url: str | None,
        model: str | None,
        api_key_encrypted: str | None,
        api_key_hint: str | None,
        timeout_seconds: int | None,
        max_retries: int | None,
        enabled: bool,
        extra: dict | None,
        updated_by: str,
    ) -> AgentApiConfig:
        """Insert or update a row by user and api_type; returns the persisted entity."""

        payload = {
            "user_public_id": user_public_id,
            "api_type": api_type,
            "display_name": display_name,
            "base_url": base_url,
            "model": model,
            "api_key_encrypted": api_key_encrypted,
            "api_key_hint": api_key_hint,
            "timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
            "enabled": enabled,
            "extra": extra,
            "updated_by": updated_by,
        }
        stmt = mysql_insert(AgentApiConfigModel).values(**payload)
        stmt = stmt.on_duplicate_key_update(
            display_name=stmt.inserted.display_name,
            base_url=stmt.inserted.base_url,
            model=stmt.inserted.model,
            api_key_encrypted=stmt.inserted.api_key_encrypted,
            api_key_hint=stmt.inserted.api_key_hint,
            timeout_seconds=stmt.inserted.timeout_seconds,
            max_retries=stmt.inserted.max_retries,
            enabled=stmt.inserted.enabled,
            extra=stmt.inserted.extra,
            updated_by=stmt.inserted.updated_by,
        )
        await self._session.execute(stmt)
        return await self._require_by_type(user_public_id, api_type)

    async def _require_by_type(self, user_public_id: str, api_type: str) -> AgentApiConfig:
        entity = await self.get_by_type(user_public_id, api_type)
        if entity is None:
            raise RuntimeError(
                f"agent_api_config upsert failed for user={user_public_id}, api_type={api_type}"
            )
        return entity

    @staticmethod
    def _to_entity(model: AgentApiConfigModel) -> AgentApiConfig:
        return AgentApiConfig(
            id=model.id,
            user_public_id=model.user_public_id,
            api_type=model.api_type,
            display_name=model.display_name,
            base_url=model.base_url,
            model=model.model,
            api_key_encrypted=model.api_key_encrypted,
            api_key_hint=model.api_key_hint,
            timeout_seconds=model.timeout_seconds,
            max_retries=model.max_retries,
            enabled=model.enabled,
            extra=model.extra,
            updated_by=model.updated_by,
            updated_at=model.updated_at,
            created_at=model.created_at,
        )
