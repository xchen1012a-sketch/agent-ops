"""SQLAlchemy repository for identity mirrors and query threads."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.domain.entities.identity import (
    QueryThread,
    ThreadStatus,
    UserMirror,
    UserRole,
)
from data_query_agent.infrastructure.db.models.identity import (
    QueryThreadModel,
    UserMirrorModel,
)


class SqlAlchemyIdentityRepository:
    """SQLAlchemy implementation of the identity repository port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_external_subject(self, external_subject: str) -> UserMirror | None:
        result = await self._session.execute(
            select(UserMirrorModel).where(UserMirrorModel.external_subject == external_subject)
        )
        model = result.scalar_one_or_none()
        return _to_user_entity(model) if model is not None else None

    async def create_user(
        self,
        *,
        public_id: str,
        external_subject: str,
        role: UserRole,
        display_name: str | None,
    ) -> UserMirror:
        now = _utcnow_naive()
        model = UserMirrorModel(
            public_id=public_id,
            external_subject=external_subject,
            role=role.value,
            display_name=display_name,
            created_at=now,
            updated_at=now,
            last_seen_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_user_entity(model)

    async def touch_user(self, user_id: int) -> UserMirror:
        model = await self._session.get(UserMirrorModel, user_id)
        if model is None:
            raise LookupError(f"user mirror not found: {user_id}")
        now = _utcnow_naive()
        model.last_seen_at = now
        model.updated_at = now
        await self._session.flush()
        return _to_user_entity(model)

    async def create_thread(
        self,
        *,
        public_id: str,
        user_id: int,
        title: str | None,
    ) -> QueryThread:
        now = _utcnow_naive()
        model = QueryThreadModel(
            public_id=public_id,
            user_id=user_id,
            title=title,
            status=ThreadStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_thread_entity(model)

    async def get_thread_for_user(
        self,
        *,
        thread_public_id: str,
        user_id: int,
    ) -> QueryThread | None:
        result = await self._session.execute(
            select(QueryThreadModel).where(
                QueryThreadModel.public_id == thread_public_id,
                QueryThreadModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return _to_thread_entity(model) if model is not None else None

    async def list_threads_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[QueryThread]:
        result = await self._session.execute(
            select(QueryThreadModel)
            .where(QueryThreadModel.user_id == user_id)
            .order_by(QueryThreadModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return tuple(_to_thread_entity(model) for model in result.scalars().all())


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _to_user_entity(model: UserMirrorModel) -> UserMirror:
    return UserMirror(
        id=model.id,
        public_id=model.public_id,
        external_subject=model.external_subject,
        role=UserRole(model.role),
        display_name=model.display_name,
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_seen_at=model.last_seen_at,
    )


def _to_thread_entity(model: QueryThreadModel) -> QueryThread:
    return QueryThread(
        id=model.id,
        public_id=model.public_id,
        user_id=model.user_id,
        title=model.title,
        status=ThreadStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
