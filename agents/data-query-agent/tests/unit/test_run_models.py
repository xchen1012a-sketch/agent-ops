"""Unit tests for query run ORM metadata."""

from __future__ import annotations

from data_query_agent.infrastructure.db.base import Base
from data_query_agent.infrastructure.db.models.run import NodeRunModel, QueryRunModel


def test_run_tables_are_registered_in_metadata() -> None:
    assert "query_runs" in Base.metadata.tables
    assert "node_runs" in Base.metadata.tables


def test_query_run_model_has_ownership_foreign_keys_and_indexes() -> None:
    table = QueryRunModel.__table__

    thread_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.thread_id.foreign_keys
    }
    user_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.user_id.foreign_keys
    }
    message_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.question_message_id.foreign_keys
    }

    assert thread_foreign_keys == {"query_threads"}
    assert user_foreign_keys == {"user_mirrors"}
    assert message_foreign_keys == {"thread_messages"}
    assert table.c.public_id.unique is True
    assert table.c.status.default is not None
    assert {
        "ix_query_runs_thread_created",
        "ix_query_runs_user_status_created",
    }.issubset({index.name for index in table.indexes})


def test_node_run_model_has_run_foreign_key_and_trace_indexes() -> None:
    table = NodeRunModel.__table__

    run_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.run_id.foreign_keys
    }

    assert run_foreign_keys == {"query_runs"}
    assert table.c.public_id.unique is True
    assert table.c.status.default is not None
    assert table.c.attempt.default is not None
    assert {
        "ix_node_runs_run_created",
        "ix_node_runs_run_node_attempt",
    }.issubset({index.name for index in table.indexes})
