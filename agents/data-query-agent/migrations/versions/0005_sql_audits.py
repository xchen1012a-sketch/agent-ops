"""Add SQL audits.

Revision ID: 0005_sql_audits
Revises: 0004_query_runs_node_runs
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_sql_audits"
down_revision: str | None = "0004_query_runs_node_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create SQL audit table."""
    op.create_table(
        "sql_audits",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("sql_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("generated_sql", sa.Text(), nullable=True),
        sa.Column("redacted_summary", sa.String(length=1000), nullable=False),
        sa.Column("policy_summary", sa.String(length=1000), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("result_summary", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["query_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_mirrors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_sql_audits_public_id"),
    )
    op.create_index(
        "ix_sql_audits_user_created",
        "sql_audits",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_sql_audits_decision_created",
        "sql_audits",
        ["decision", "created_at"],
        unique=False,
    )
    op.create_index("ix_sql_audits_expires_at", "sql_audits", ["expires_at"], unique=False)


def downgrade() -> None:
    """Drop SQL audit table."""
    op.drop_index("ix_sql_audits_expires_at", table_name="sql_audits")
    op.drop_index("ix_sql_audits_decision_created", table_name="sql_audits")
    op.drop_index("ix_sql_audits_user_created", table_name="sql_audits")
    op.drop_table("sql_audits")
