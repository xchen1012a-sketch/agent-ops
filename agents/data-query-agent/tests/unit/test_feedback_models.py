"""Unit tests for feedback ORM metadata."""

from __future__ import annotations

from data_query_agent.infrastructure.db.base import Base
from data_query_agent.infrastructure.db.models.feedback import (
    FollowupSuggestionModel,
    QueryFeedbackModel,
)


def test_feedback_tables_are_registered_in_metadata() -> None:
    assert "feedbacks" in Base.metadata.tables
    assert "followup_suggestions" in Base.metadata.tables


def test_feedback_model_has_scope_foreign_keys_and_unique_constraint() -> None:
    table = QueryFeedbackModel.__table__

    run_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.run_id.foreign_keys
    }
    thread_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.thread_id.foreign_keys
    }
    user_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.user_id.foreign_keys
    }
    unique_constraints = {constraint.name for constraint in table.constraints}

    assert run_foreign_keys == {"query_runs"}
    assert thread_foreign_keys == {"query_threads"}
    assert user_foreign_keys == {"user_mirrors"}
    assert "uq_feedbacks_run_user" in unique_constraints
    assert {
        "ix_feedbacks_user_created",
        "ix_feedbacks_run",
    }.issubset({index.name for index in table.indexes})


def test_followup_suggestion_model_has_run_thread_indexes() -> None:
    table = FollowupSuggestionModel.__table__

    run_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.run_id.foreign_keys
    }
    thread_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.thread_id.foreign_keys
    }
    user_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.user_id.foreign_keys
    }

    assert run_foreign_keys == {"query_runs"}
    assert thread_foreign_keys == {"query_threads"}
    assert user_foreign_keys == {"user_mirrors"}
    assert table.c.public_id.unique is True
    assert {
        "ix_followup_suggestions_run_rank",
        "ix_followup_suggestions_thread_rank",
        "ix_followup_suggestions_user_created",
    }.issubset({index.name for index in table.indexes})
