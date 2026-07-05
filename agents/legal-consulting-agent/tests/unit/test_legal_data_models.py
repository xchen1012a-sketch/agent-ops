"""Unit tests for LEGAL-130 ORM metadata."""

from __future__ import annotations

from legal_consulting_agent.infrastructure.db.base import Base
from legal_consulting_agent.infrastructure.db.models import (
    AgentRunModel,
    LegalCategoryModel,
    LegalMessageModel,
    LegalSessionModel,
    NodeRunModel,
    UserModel,
)


def test_legal_130_tables_are_registered() -> None:
    tables = Base.metadata.tables

    assert {
        "users",
        "legal_categories",
        "sessions",
        "messages",
        "agent_runs",
        "node_runs",
    }.issubset(tables.keys())


def test_user_model_does_not_store_password_fields() -> None:
    columns = set(UserModel.__table__.columns.keys())

    assert "password" not in columns
    assert "password_hash" not in columns
    assert "refresh_token" not in columns


def test_session_and_message_foreign_keys_enforce_ownership_path() -> None:
    session_fks = {
        fk.constraint.name
        for column in LegalSessionModel.__table__.columns
        for fk in column.foreign_keys
    }
    message_fks = {
        fk.constraint.name
        for column in LegalMessageModel.__table__.columns
        for fk in column.foreign_keys
    }

    assert {"fk_sessions_user", "fk_sessions_category"}.issubset(session_fks)
    assert "fk_messages_session" in message_fks


def test_run_and_node_run_tables_have_audit_indexes() -> None:
    run_indexes = {index.name for index in AgentRunModel.__table__.indexes}
    node_indexes = {index.name for index in NodeRunModel.__table__.indexes}
    category_columns = set(LegalCategoryModel.__table__.columns.keys())

    assert {"idx_runs_thread", "idx_runs_status"}.issubset(run_indexes)
    assert "idx_node_runs_run" in node_indexes
    assert {"code", "display_name", "sort_order"}.issubset(category_columns)
