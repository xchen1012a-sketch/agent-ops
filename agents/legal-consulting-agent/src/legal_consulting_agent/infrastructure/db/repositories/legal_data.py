"""SQLAlchemy repository for LEGAL-130 identity and data records."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from legal_consulting_agent.domain.entities.legal_data import (
    AgentRun,
    LegalCategory,
    LegalMessage,
    LegalSession,
    NodeRun,
    UserMirror,
)
from legal_consulting_agent.infrastructure.db.models.legal_data import (
    AgentRunModel,
    LegalCategoryModel,
    LegalMessageModel,
    LegalSessionModel,
    NodeRunModel,
    UserModel,
)


class SqlAlchemyLegalDataRepository:
    """Persist LEGAL-130 records using an externally managed session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_user_mirror(self, user: UserMirror) -> UserMirror:
        """Create or update a user mirror by public ID without committing."""
        existing = await self._get_user_model_by_public_id(user.public_id)
        if existing is None:
            existing = UserModel(
                public_id=user.public_id,
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                status=user.status,
            )
            self._session.add(existing)
        else:
            existing.email = user.email
            existing.display_name = user.display_name
            existing.role = user.role
            existing.status = user.status

        await self._session.flush()
        return self._to_user(existing)

    async def get_user_by_public_id(self, public_id: str) -> UserMirror | None:
        """Return a user mirror by public ID."""
        model = await self._get_user_model_by_public_id(public_id)
        return self._to_user(model) if model is not None else None

    async def get_category_by_code(self, code: str) -> LegalCategory | None:
        """Return a legal category by code."""
        result = await self._session.execute(
            select(LegalCategoryModel).where(LegalCategoryModel.code == code)
        )
        model = result.scalar_one_or_none()
        return self._to_category(model) if model is not None else None

    async def create_session(self, session: LegalSession) -> LegalSession:
        """Persist a consultation session."""
        model = LegalSessionModel(
            public_id=session.public_id,
            user_id=session.user_id,
            category_id=session.category_id,
            title=session.title,
            status=session.status,
            last_message_at=session.last_message_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_session(model)

    async def get_session_for_user(
        self,
        *,
        session_public_id: str,
        user_id: int,
    ) -> LegalSession | None:
        """Return a user-owned session or None when absent/unauthorized."""
        result = await self._session.execute(
            select(LegalSessionModel).where(
                LegalSessionModel.public_id == session_public_id,
                LegalSessionModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_session(model) if model is not None else None

    async def append_message(self, message: LegalMessage) -> LegalMessage:
        """Persist one message inside an existing session."""
        model = LegalMessageModel(
            public_id=message.public_id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            high_risk=message.high_risk,
            prompt_version=message.prompt_version,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_message(model)

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        """Persist an Agent run audit record."""
        model = AgentRunModel(
            public_id=run.public_id,
            thread_id=run.thread_id,
            user_id=run.user_id,
            workflow_version=run.workflow_version,
            prompt_version=run.prompt_version,
            status=run.status,
            retry_count=run.retry_count,
            error_code=run.error_code,
            error_summary=run.error_summary,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_ms=run.duration_ms,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_agent_run(model)

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        """Persist an Agent node audit record."""
        model = NodeRunModel(
            run_id=node_run.run_id,
            node_name=node_run.node_name,
            status=node_run.status,
            duration_ms=node_run.duration_ms,
            error_code=node_run.error_code,
            metadata_json=node_run.metadata,
            started_at=node_run.started_at,
            finished_at=node_run.finished_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_node_run(model)

    async def _get_user_model_by_public_id(self, public_id: str) -> UserModel | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.public_id == public_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_user(model: UserModel) -> UserMirror:
        return UserMirror(
            id=model.id,
            public_id=model.public_id,
            email=model.email,
            display_name=model.display_name,
            role=model.role,
            status=model.status,
        )

    @staticmethod
    def _to_category(model: LegalCategoryModel) -> LegalCategory:
        return LegalCategory(
            id=model.id,
            public_id=model.public_id,
            code=model.code,
            display_name=model.display_name,
            description=model.description,
            sort_order=model.sort_order,
        )

    @staticmethod
    def _to_session(model: LegalSessionModel) -> LegalSession:
        return LegalSession(
            id=model.id,
            public_id=model.public_id,
            user_id=model.user_id,
            category_id=model.category_id,
            title=model.title,
            status=model.status,
            last_message_at=model.last_message_at,
        )

    @staticmethod
    def _to_message(model: LegalMessageModel) -> LegalMessage:
        return LegalMessage(
            id=model.id,
            public_id=model.public_id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            citations=model.citations,
            high_risk=model.high_risk,
            prompt_version=model.prompt_version,
        )

    @staticmethod
    def _to_agent_run(model: AgentRunModel) -> AgentRun:
        return AgentRun(
            id=model.id,
            public_id=model.public_id,
            thread_id=model.thread_id,
            user_id=model.user_id,
            workflow_version=model.workflow_version,
            prompt_version=model.prompt_version,
            status=model.status,
            retry_count=model.retry_count,
            error_code=model.error_code,
            error_summary=model.error_summary,
            started_at=model.started_at,
            finished_at=model.finished_at,
            duration_ms=model.duration_ms,
        )

    @staticmethod
    def _to_node_run(model: NodeRunModel) -> NodeRun:
        return NodeRun(
            id=model.id,
            run_id=model.run_id,
            node_name=model.node_name,
            status=model.status,
            duration_ms=model.duration_ms,
            error_code=model.error_code,
            metadata=model.metadata_json,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )
