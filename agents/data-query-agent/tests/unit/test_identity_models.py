"""Unit tests for identity ORM metadata."""

from __future__ import annotations

from data_query_agent.infrastructure.db.base import Base
from data_query_agent.infrastructure.db.models.identity import (
    QueryThreadModel,
    ThreadMessageModel,
    UserMirrorModel,
)


def test_identity_tables_are_registered_in_metadata() -> None:
    assert "user_mirrors" in Base.metadata.tables
    assert "query_threads" in Base.metadata.tables
    assert "thread_messages" in Base.metadata.tables


def test_user_mirror_model_constraints_and_indexes() -> None:
    table = UserMirrorModel.__table__

    assert table.c.public_id.unique is True
    assert table.c.external_subject.nullable is False
    assert table.c.role.default is not None
    assert "ix_user_mirrors_external_subject" in {index.name for index in table.indexes}


def test_query_thread_model_has_user_foreign_key_and_index() -> None:
    table = QueryThreadModel.__table__

    foreign_keys = {foreign_key.column.table.name for foreign_key in table.c.user_id.foreign_keys}
    assert foreign_keys == {"user_mirrors"}
    assert table.c.public_id.unique is True
    assert "ix_query_threads_user_created" in {index.name for index in table.indexes}


def test_thread_message_model_has_thread_and_user_foreign_keys() -> None:
    table = ThreadMessageModel.__table__

    thread_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.thread_id.foreign_keys
    }
    user_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.user_id.foreign_keys
    }
    assert thread_foreign_keys == {"query_threads"}
    assert user_foreign_keys == {"user_mirrors"}
    assert table.c.public_id.unique is True
    assert {
        "ix_thread_messages_thread_created",
        "ix_thread_messages_user_created",
    }.issubset({index.name for index in table.indexes})
