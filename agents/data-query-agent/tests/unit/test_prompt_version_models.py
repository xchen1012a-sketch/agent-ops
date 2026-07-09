"""Unit tests for prompt version ORM metadata."""

from __future__ import annotations

from data_query_agent.infrastructure.db.base import Base
from data_query_agent.infrastructure.db.models.prompt_version import PromptVersionModel


def test_prompt_version_table_is_registered_in_metadata() -> None:
    assert "prompt_versions" in Base.metadata.tables


def test_prompt_version_model_has_admin_foreign_key_and_unique_version() -> None:
    table = PromptVersionModel.__table__

    created_by_foreign_keys = {
        foreign_key.column.table.name for foreign_key in table.c.created_by_user_id.foreign_keys
    }
    unique_constraints = {constraint.name for constraint in table.constraints}

    assert created_by_foreign_keys == {"user_mirrors"}
    assert table.c.public_id.unique is True
    assert table.c.template_body.nullable is False
    assert table.c.variables_schema.nullable is False
    assert table.c.output_schema.nullable is False
    assert "uq_prompt_versions_name_version" in unique_constraints
    assert {
        "ix_prompt_versions_name_active",
        "ix_prompt_versions_created_by",
    }.issubset({index.name for index in table.indexes})
