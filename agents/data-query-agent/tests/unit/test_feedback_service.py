"""Unit tests for feedback and follow-up suggestion service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from data_query_agent.application.services.feedback_service import FeedbackService
from data_query_agent.domain.entities.feedback import (
    FeedbackRating,
    FollowupSuggestion,
    QueryFeedback,
)
from data_query_agent.domain.entities.identity import (
    QueryThread,
    ThreadStatus,
    UserMirror,
    UserRole,
)
from data_query_agent.domain.entities.run import QueryRun, RunStatus


class FakeFeedbackRepository:
    """In-memory feedback repository for service tests."""

    def __init__(self) -> None:
        self.feedbacks: list[QueryFeedback] = []
        self.suggestions: list[FollowupSuggestion] = []
        self.next_feedback_id = 1
        self.next_suggestion_id = 1

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
        feedback = QueryFeedback(
            id=self.next_feedback_id,
            public_id=public_id,
            run_id=run_id,
            thread_id=thread_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.next_feedback_id += 1
        self.feedbacks.append(feedback)
        return feedback

    async def list_feedback_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[QueryFeedback]:
        owned = [feedback for feedback in self.feedbacks if feedback.user_id == user_id]
        return tuple(owned[offset : offset + limit])

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
        suggestion = FollowupSuggestion(
            id=self.next_suggestion_id,
            public_id=public_id,
            run_id=run_id,
            thread_id=thread_id,
            user_id=user_id,
            suggestion_text=suggestion_text,
            rank=rank,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.next_suggestion_id += 1
        self.suggestions.append(suggestion)
        return suggestion

    async def list_followup_suggestions_for_run(
        self,
        *,
        run_id: int,
        user_id: int,
    ) -> Sequence[FollowupSuggestion]:
        owned = [
            suggestion
            for suggestion in self.suggestions
            if suggestion.run_id == run_id and suggestion.user_id == user_id
        ]
        return tuple(sorted(owned, key=lambda suggestion: suggestion.rank))

    async def list_followup_suggestions_for_thread(
        self,
        *,
        thread_id: int,
        user_id: int,
    ) -> Sequence[FollowupSuggestion]:
        owned = [
            suggestion
            for suggestion in self.suggestions
            if suggestion.thread_id == thread_id and suggestion.user_id == user_id
        ]
        return tuple(sorted(owned, key=lambda suggestion: suggestion.rank))


def _run(*, run_id: int = 10, thread_id: int = 30, user_id: int = 20) -> QueryRun:
    now = datetime.now(UTC).replace(tzinfo=None)
    return QueryRun(
        id=run_id,
        public_id=f"run-{run_id}",
        thread_id=thread_id,
        user_id=user_id,
        status=RunStatus.SUCCESS,
        question_message_id=None,
        error_code=None,
        error_message=None,
        started_at=now,
        finished_at=now,
        created_at=now,
        updated_at=now,
    )


def _thread(*, thread_id: int = 30, user_id: int = 20) -> QueryThread:
    now = datetime.now(UTC).replace(tzinfo=None)
    return QueryThread(
        id=thread_id,
        public_id=f"thread-{thread_id}",
        user_id=user_id,
        title=None,
        status=ThreadStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def _user(*, user_id: int = 20) -> UserMirror:
    now = datetime.now(UTC).replace(tzinfo=None)
    return UserMirror(
        id=user_id,
        public_id=f"user-{user_id}",
        external_subject=f"subject-{user_id}",
        role=UserRole.USER,
        display_name=None,
        created_at=now,
        updated_at=now,
        last_seen_at=now,
    )


@pytest.mark.asyncio
async def test_create_feedback_for_run_keeps_run_and_user_scope() -> None:
    service = FeedbackService(FakeFeedbackRepository())

    feedback = await service.create_feedback_for_run(
        run=_run(),
        rating=FeedbackRating.HELPFUL,
        comment="answer was useful",
    )

    assert feedback.run_id == 10
    assert feedback.thread_id == 30
    assert feedback.user_id == 20
    assert feedback.rating is FeedbackRating.HELPFUL
    assert feedback.comment == "answer was useful"


@pytest.mark.asyncio
async def test_list_feedback_for_user_blocks_other_users() -> None:
    repository = FakeFeedbackRepository()
    service = FeedbackService(repository)
    owner_feedback = await service.create_feedback_for_run(
        run=_run(user_id=20),
        rating=FeedbackRating.HELPFUL,
    )
    await service.create_feedback_for_run(
        run=_run(run_id=11, user_id=21),
        rating=FeedbackRating.NOT_HELPFUL,
    )

    feedbacks = await service.list_feedback_for_user(user=_user(user_id=20))

    assert feedbacks == (owner_feedback,)


@pytest.mark.asyncio
async def test_followup_suggestions_can_be_listed_by_run_and_thread() -> None:
    service = FeedbackService(FakeFeedbackRepository())
    run = _run()
    thread = _thread()

    second = await service.create_followup_suggestion_for_run(
        run=run,
        suggestion_text="按地区拆分看看",
        rank=2,
    )
    first = await service.create_followup_suggestion_for_run(
        run=run,
        suggestion_text="查看趋势",
        rank=1,
    )
    thread_only = await service.create_followup_suggestion_for_thread(
        thread=thread,
        suggestion_text="对比上期",
        rank=3,
    )

    run_suggestions = await service.list_followup_suggestions_for_run(run=run)
    thread_suggestions = await service.list_followup_suggestions_for_thread(thread=thread)

    assert run_suggestions == (first, second)
    assert thread_suggestions == (first, second, thread_only)


@pytest.mark.asyncio
async def test_followup_suggestions_keep_user_scope() -> None:
    service = FeedbackService(FakeFeedbackRepository())
    owner = _run(user_id=20)
    other = _run(run_id=11, user_id=21)
    owner_suggestion = await service.create_followup_suggestion_for_run(
        run=owner,
        suggestion_text="owner suggestion",
        rank=1,
    )
    await service.create_followup_suggestion_for_run(
        run=other,
        suggestion_text="other suggestion",
        rank=1,
    )

    suggestions = await service.list_followup_suggestions_for_run(run=owner)

    assert suggestions == (owner_suggestion,)


@pytest.mark.asyncio
async def test_rejects_unpersisted_models_and_invalid_rank() -> None:
    service = FeedbackService(FakeFeedbackRepository())
    now = datetime.now(UTC).replace(tzinfo=None)
    unpersisted_run = QueryRun(
        id=None,
        public_id="run-none",
        thread_id=30,
        user_id=20,
        status=RunStatus.PENDING,
        question_message_id=None,
        error_code=None,
        error_message=None,
        started_at=None,
        finished_at=None,
        created_at=now,
        updated_at=now,
    )
    unpersisted_thread = QueryThread(
        id=None,
        public_id="thread-none",
        user_id=20,
        title=None,
        status=ThreadStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(ValueError):
        await service.create_feedback_for_run(
            run=unpersisted_run,
            rating=FeedbackRating.HELPFUL,
        )
    with pytest.raises(ValueError):
        await service.create_followup_suggestion_for_run(
            run=_run(),
            suggestion_text="invalid",
            rank=0,
        )
    with pytest.raises(ValueError):
        await service.create_followup_suggestion_for_thread(
            thread=unpersisted_thread,
            suggestion_text="invalid",
            rank=1,
        )
