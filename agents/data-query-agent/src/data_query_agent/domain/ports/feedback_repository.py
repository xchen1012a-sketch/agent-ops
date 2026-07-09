"""Repository port for feedback and follow-up suggestions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from data_query_agent.domain.entities.feedback import (
    FeedbackRating,
    FollowupSuggestion,
    QueryFeedback,
)


class FeedbackRepository(Protocol):
    """Persistence boundary for feedback and follow-up suggestions."""

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
        """Create user feedback for one owned query run."""

    async def list_feedback_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[QueryFeedback]:
        """List feedback records owned by one user."""

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
        """Create one follow-up suggestion for an owned run or thread."""

    async def list_followup_suggestions_for_run(
        self,
        *,
        run_id: int,
        user_id: int,
    ) -> Sequence[FollowupSuggestion]:
        """List follow-up suggestions for one owned run."""

    async def list_followup_suggestions_for_thread(
        self,
        *,
        thread_id: int,
        user_id: int,
    ) -> Sequence[FollowupSuggestion]:
        """List follow-up suggestions for one owned thread."""
