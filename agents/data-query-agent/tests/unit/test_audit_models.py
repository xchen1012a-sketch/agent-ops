"""Unit tests for SQL audit ORM metadata."""

from __future__ import annotations

from data_query_agent.infrastructure.db.base import Base
from data_query_agent.infrastructure.db.models.audit import SqlAuditModel


def test_sql_audit_table_is_registered_in_metadata() -> None:
    assert "sql_audits" in Base.metadata.tables


def test_sql_audit_model_has_run_user_foreign_keys_and_indexes() -> None:
    table = SqlAuditModel.__table__

    run_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.run_id.foreign_keys
    }
    user_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.user_id.foreign_keys
    }

    assert run_foreign_keys == {"query_runs"}
    assert user_foreign_keys == {"user_mirrors"}
    assert table.c.public_id.unique is True
    assert table.c.expires_at.nullable is False
    assert {
        "ix_sql_audits_user_created",
        "ix_sql_audits_decision_created",
        "ix_sql_audits_expires_at",
    }.issubset({index.name for index in table.indexes})
