"""Domain entities for user feedback and follow-up suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class FeedbackRating(StrEnum):
    """User feedback rating for one query run."""

    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


@dataclass(frozen=True, slots=True)
class QueryFeedback:
    """User feedback attached to a query run."""

    id: int | None
    public_id: str
    run_id: int
    thread_id: int
    user_id: int
    rating: FeedbackRating
    comment: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class FollowupSuggestion:
    """Suggested follow-up question for one run or thread."""

    id: int | None
    public_id: str
    run_id: int | None
    thread_id: int
    user_id: int
    suggestion_text: str
    rank: int
    created_at: datetime
