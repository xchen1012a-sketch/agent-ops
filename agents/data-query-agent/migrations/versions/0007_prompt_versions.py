"""Add prompt versions.

Revision ID: 0007_prompt_versions
Revises: 0006_feedbacks_followups
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_prompt_versions"
down_revision: str | None = "0006_feedbacks_followups"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create prompt version table."""
    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("prompt_name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("template_hash", sa.String(length=128), nullable=False),
        sa.Column("template_body", sa.Text(), nullable=False),
        sa.Column("variables_schema", sa.Text(), nullable=False),
        sa.Column("output_schema", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["user_mirrors.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_prompt_versions_public_id"),
        sa.UniqueConstraint("prompt_name", "version", name="uq_prompt_versions_name_version"),
    )
    op.create_index(
        "ix_prompt_versions_name_active",
        "prompt_versions",
        ["prompt_name", "is_active"],
    )
    op.create_index(
        "ix_prompt_versions_created_by",
        "prompt_versions",
        ["created_by_user_id", "created_at"],
    )


def downgrade() -> None:
    """Drop prompt version table."""
    op.drop_index("ix_prompt_versions_created_by", table_name="prompt_versions")
    op.drop_index("ix_prompt_versions_name_active", table_name="prompt_versions")
    op.drop_table("prompt_versions")
