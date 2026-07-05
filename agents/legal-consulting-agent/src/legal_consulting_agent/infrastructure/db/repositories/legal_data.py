"""SQLAlchemy repository for LEGAL-130 identity and data records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from legal_consulting_agent.domain.entities.legal_data import (
    AgentRun,
    ConsultationRecord,
    Feedback,
    HighRiskReview,
    KnowledgeMaterial,
    LegalCategory,
    LegalMessage,
    LegalSession,
    NodeRun,
    PromptVersion,
    UserMirror,
)
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole, ReviewStatus
from legal_consulting_agent.infrastructure.db.models.legal_data import (
    AgentRunModel,
    ConsultationRecordModel,
    FeedbackModel,
    HighRiskReviewModel,
    KnowledgeMaterialModel,
    LegalCategoryModel,
    LegalMessageModel,
    LegalSessionModel,
    NodeRunModel,
    PromptVersionModel,
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

    async def get_message_for_session(
        self,
        *,
        message_public_id: str,
        session_id: int,
        role: MessageRole,
    ) -> LegalMessage | None:
        """Return a message only when its session and role match."""
        result = await self._session.execute(
            select(LegalMessageModel).where(
                LegalMessageModel.public_id == message_public_id,
                LegalMessageModel.session_id == session_id,
                LegalMessageModel.role == role,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_message(model) if model is not None else None

    async def list_messages_for_user_session(
        self,
        *,
        session_public_id: str,
        user_id: int,
        limit: int,
        offset: int,
    ) -> list[LegalMessage]:
        """Return messages from a user-owned session ordered by id."""
        result = await self._session.execute(
            select(LegalMessageModel)
            .join(LegalSessionModel, LegalMessageModel.session_id == LegalSessionModel.id)
            .where(
                LegalSessionModel.public_id == session_public_id,
                LegalSessionModel.user_id == user_id,
            )
            .order_by(LegalMessageModel.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_message(model) for model in result.scalars().all()]

    async def create_consultation_record(
        self,
        record: ConsultationRecord,
    ) -> ConsultationRecord:
        """Persist a completed consultation snapshot without committing."""
        model = ConsultationRecordModel(
            public_id=record.public_id,
            user_id=record.user_id,
            session_id=record.session_id,
            category_id=record.category_id,
            question_message_id=record.question_message_id,
            answer_message_id=record.answer_message_id,
            summary=record.summary,
            citations=record.citations,
            high_risk=record.high_risk,
            disclaimer=record.disclaimer,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_consultation_record(model)

    async def get_consultation_record_for_user(
        self,
        *,
        record_public_id: str,
        user_id: int,
    ) -> ConsultationRecord | None:
        """Return a user-owned consultation record, or None."""
        result = await self._session.execute(
            select(ConsultationRecordModel).where(
                ConsultationRecordModel.public_id == record_public_id,
                ConsultationRecordModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_consultation_record(model) if model is not None else None

    async def list_consultation_records_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
        query: str | None,
    ) -> list[ConsultationRecord]:
        """Return user-owned consultation records ordered by newest first."""
        statement = select(ConsultationRecordModel).where(
            ConsultationRecordModel.user_id == user_id
        )
        if query is not None:
            statement = statement.where(
                ConsultationRecordModel.summary.contains(query, autoescape=True)
            )
        result = await self._session.execute(
            statement.order_by(ConsultationRecordModel.id.desc()).limit(limit).offset(offset)
        )
        return [self._to_consultation_record(model) for model in result.scalars().all()]

    async def create_feedback(self, feedback: Feedback) -> Feedback:
        """Persist user feedback without committing."""
        model = FeedbackModel(
            message_id=feedback.message_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_feedback(model)

    async def create_high_risk_review(self, review: HighRiskReview) -> HighRiskReview:
        """Persist a pending high-risk review without committing."""
        model = HighRiskReviewModel(
            message_id=review.message_id,
            user_id=review.user_id,
            reason=review.reason,
            status=review.status,
            reviewed_by=review.reviewed_by,
            resolution=review.resolution,
            reviewed_at=review.reviewed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_high_risk_review(model)

    async def list_high_risk_reviews(
        self,
        *,
        status: ReviewStatus,
        limit: int,
        offset: int,
    ) -> list[HighRiskReview]:
        """Return high-risk reviews for administrator queues."""
        result = await self._session.execute(
            select(HighRiskReviewModel)
            .where(HighRiskReviewModel.status == status)
            .order_by(HighRiskReviewModel.id.asc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_high_risk_review(model) for model in result.scalars().all()]

    async def update_high_risk_review_resolution(
        self,
        *,
        review_id: int,
        reviewer_id: int,
        status: ReviewStatus,
        resolution: str,
        reviewed_at: datetime,
    ) -> HighRiskReview | None:
        """Persist an administrator review resolution without committing."""
        result = await self._session.execute(
            select(HighRiskReviewModel).where(HighRiskReviewModel.id == review_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.status = status
        model.reviewed_by = reviewer_id
        model.resolution = resolution
        model.reviewed_at = reviewed_at
        await self._session.flush()
        return self._to_high_risk_review(model)

    async def create_prompt_version(self, prompt: PromptVersion) -> PromptVersion:
        """Persist Prompt metadata without committing."""
        model = PromptVersionModel(
            prompt_name=prompt.prompt_name,
            version=prompt.version,
            template_key=prompt.template_key,
            variables=prompt.variables,
            output_schema=prompt.output_schema,
            status=prompt.status,
            created_by=prompt.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_prompt_version(model)

    async def create_knowledge_material(
        self,
        material: KnowledgeMaterial,
    ) -> KnowledgeMaterial:
        """Persist knowledge material metadata without committing."""
        model = KnowledgeMaterialModel(
            public_id=material.public_id,
            category_id=material.category_id,
            title=material.title,
            source_name=material.source_name,
            source_section=material.source_section,
            file_hash=material.file_hash,
            file_key=material.file_key,
            chunk_count=material.chunk_count,
            status=material.status,
            version=material.version,
            uploaded_by=material.uploaded_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_knowledge_material(model)

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
    def _to_consultation_record(model: ConsultationRecordModel) -> ConsultationRecord:
        return ConsultationRecord(
            id=model.id,
            public_id=model.public_id,
            user_id=model.user_id,
            session_id=model.session_id,
            category_id=model.category_id,
            question_message_id=model.question_message_id,
            answer_message_id=model.answer_message_id,
            summary=model.summary,
            citations=model.citations,
            high_risk=model.high_risk,
            disclaimer=model.disclaimer,
        )

    @staticmethod
    def _to_feedback(model: FeedbackModel) -> Feedback:
        return Feedback(
            id=model.id,
            message_id=model.message_id,
            user_id=model.user_id,
            rating=model.rating,
            comment=model.comment,
        )

    @staticmethod
    def _to_high_risk_review(model: HighRiskReviewModel) -> HighRiskReview:
        return HighRiskReview(
            id=model.id,
            message_id=model.message_id,
            user_id=model.user_id,
            reason=model.reason,
            status=model.status,
            reviewed_by=model.reviewed_by,
            resolution=model.resolution,
            reviewed_at=model.reviewed_at,
        )

    @staticmethod
    def _to_prompt_version(model: PromptVersionModel) -> PromptVersion:
        return PromptVersion(
            id=model.id,
            prompt_name=model.prompt_name,
            version=model.version,
            template_key=model.template_key,
            variables=model.variables,
            output_schema=model.output_schema,
            status=model.status,
            created_by=model.created_by,
        )

    @staticmethod
    def _to_knowledge_material(model: KnowledgeMaterialModel) -> KnowledgeMaterial:
        return KnowledgeMaterial(
            id=model.id,
            public_id=model.public_id,
            category_id=model.category_id,
            title=model.title,
            source_name=model.source_name,
            source_section=model.source_section,
            file_hash=model.file_hash,
            file_key=model.file_key,
            chunk_count=model.chunk_count,
            status=model.status,
            version=model.version,
            uploaded_by=model.uploaded_by,
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
