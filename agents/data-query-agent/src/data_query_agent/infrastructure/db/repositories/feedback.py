"""SQLAlchemy repository for feedback and follow-up suggestions."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.domain.entities.feedback import (
    FeedbackRating,
    FollowupSuggestion,
    QueryFeedback,
)
from data_query_agent.infrastructure.db.models.feedback import (
    FollowupSuggestionModel,
    QueryFeedbackModel,
)


class SqlAlchemyFeedbackRepository:
    """SQLAlchemy implementation of the feedback repository port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_feedback(
        self,
        *,
        public_id: str,
        run_id: int,
        thread_id: int,
        user_id: int,
        rating: FeedbackRating,
        comment: str | None,
    ) -> QueryFeedback:
        model = QueryFeedbackModel(
            public_id=public_id,
            run_id=run_id,
            thread_id=thread_id,
            user_id=user_id,
            rating=rating.value,
            comment=comment,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_feedback_entity(model)

    async def list_feedback_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[QueryFeedback]:
        result = await self._session.execute(
            select(QueryFeedbackModel)
            .where(QueryFeedbackModel.user_id == user_id)
            .order_by(QueryFeedbackModel.created_at.desc(), QueryFeedbackModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return tuple(_to_feedback_entity(model) for model in result.scalars().all())

    async def create_followup_suggestion(
        self,
        *,
        public_id: str,
        thread_id: int,
        user_id: int,
        suggestion_text: str,
        rank: int,
        run_id: int | None = None,
    ) -> FollowupSuggestion:
        model = FollowupSuggestionModel(
            public_id=public_id,
            run_id=run_id,
            thread_id=thread_id,
            user_id=user_id,
            suggestion_text=suggestion_text,
            rank=rank,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_suggestion_entity(model)

    async def list_followup_suggestions_for_run(
        self,
        *,
        run_id: int,
        user_id: int,
    ) -> Sequence[FollowupSuggestion]:
        result = await self._session.execute(
            select(FollowupSuggestionModel)
            .where(
                FollowupSuggestionModel.run_id == run_id,
                FollowupSuggestionModel.user_id == user_id,
            )
            .order_by(FollowupSuggestionModel.rank.asc(), FollowupSuggestionModel.id.asc())
        )
        return tuple(_to_suggestion_entity(model) for model in result.scalars().all())

    async def list_followup_suggestions_for_thread(
        self,
        *,
        thread_id: int,
        user_id: int,
    ) -> Sequence[FollowupSuggestion]:
        result = await self._session.execute(
            select(FollowupSuggestionModel)
            .where(
                FollowupSuggestionModel.thread_id == thread_id,
                FollowupSuggestionModel.user_id == user_id,
            )
            .order_by(FollowupSuggestionModel.rank.asc(), FollowupSuggestionModel.id.asc())
        )
        return tuple(_to_suggestion_entity(model) for model in result.scalars().all())


def _to_feedback_entity(model: QueryFeedbackModel) -> QueryFeedback:
    return QueryFeedback(
        id=model.id,
        public_id=model.public_id,
        run_id=model.run_id,
        thread_id=model.thread_id,
        user_id=model.user_id,
        rating=FeedbackRating(model.rating),
        comment=model.comment,
        created_at=model.created_at,
    )


def _to_suggestion_entity(model: FollowupSuggestionModel) -> FollowupSuggestion:
    return FollowupSuggestion(
        id=model.id,
        public_id=model.public_id,
        run_id=model.run_id,
        thread_id=model.thread_id,
        user_id=model.user_id,
        suggestion_text=model.suggestion_text,
        rank=model.rank,
        created_at=model.created_at,
    )
