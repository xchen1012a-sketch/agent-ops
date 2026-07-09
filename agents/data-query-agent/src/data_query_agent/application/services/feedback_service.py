"""Application service for feedback and follow-up suggestions."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from data_query_agent.domain.entities.feedback import (
    FeedbackRating,
    FollowupSuggestion,
    QueryFeedback,
)
from data_query_agent.domain.entities.identity import QueryThread, UserMirror
from data_query_agent.domain.entities.run import QueryRun
from data_query_agent.domain.ports.feedback_repository import FeedbackRepository


class FeedbackService:
    """Use cases for user-owned feedback and follow-up suggestions."""

    def __init__(self, repository: FeedbackRepository) -> None:
        self._repository = repository

    async def create_feedback_for_run(
        self,
        *,
        run: QueryRun,
        rating: FeedbackRating,
        comment: str | None = None,
    ) -> QueryFeedback:
        """Create feedback under an already-owned query run."""
        if run.id is None:
            raise ValueError("persisted query run must have an id")
        return await self._repository.create_feedback(
            public_id=str(uuid4()),
            run_id=run.id,
            thread_id=run.thread_id,
            user_id=run.user_id,
            rating=rating,
            comment=comment,
        )

    async def list_feedback_for_user(
        self,
        *,
        user: UserMirror,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[QueryFeedback]:
        """List feedback owned by one persisted user mirror."""
        if user.id is None:
            raise ValueError("persisted user mirror must have an id")
        return await self._repository.list_feedback_for_user(
            user_id=user.id,
            limit=limit,
            offset=offset,
        )

    async def create_followup_suggestion_for_run(
        self,
        *,
        run: QueryRun,
        suggestion_text: str,
        rank: int,
    ) -> FollowupSuggestion:
        """Create a ranked follow-up suggestion for one owned query run."""
        if run.id is None:
            raise ValueError("persisted query run must have an id")
        _validate_rank(rank)
        return await self._repository.create_followup_suggestion(
            public_id=str(uuid4()),
            run_id=run.id,
            thread_id=run.thread_id,
            user_id=run.user_id,
            suggestion_text=suggestion_text,
            rank=rank,
        )

    async def create_followup_suggestion_for_thread(
        self,
        *,
        thread: QueryThread,
        suggestion_text: str,
        rank: int,
    ) -> FollowupSuggestion:
        """Create a ranked follow-up suggestion scoped to one owned thread."""
        if thread.id is None:
            raise ValueError("persisted thread must have an id")
        _validate_rank(rank)
        return await self._repository.create_followup_suggestion(
            public_id=str(uuid4()),
            run_id=None,
            thread_id=thread.id,
            user_id=thread.user_id,
            suggestion_text=suggestion_text,
            rank=rank,
        )

    async def list_followup_suggestions_for_run(
        self,
        *,
        run: QueryRun,
    ) -> Sequence[FollowupSuggestion]:
        """List suggestions for an already-owned query run."""
        if run.id is None:
            raise ValueError("persisted query run must have an id")
        return await self._repository.list_followup_suggestions_for_run(
            run_id=run.id,
            user_id=run.user_id,
        )

    async def list_followup_suggestions_for_thread(
        self,
        *,
        thread: QueryThread,
    ) -> Sequence[FollowupSuggestion]:
        """List suggestions for an already-owned query thread."""
        if thread.id is None:
            raise ValueError("persisted thread must have an id")
        return await self._repository.list_followup_suggestions_for_thread(
            thread_id=thread.id,
            user_id=thread.user_id,
        )


def _validate_rank(rank: int) -> None:
    if rank < 1:
        raise ValueError("follow-up suggestion rank must be positive")
