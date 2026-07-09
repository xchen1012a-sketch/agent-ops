"""Add feedbacks and follow-up suggestions.

Revision ID: 0006_feedbacks_followups
Revises: 0005_sql_audits
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_feedbacks_followups"
down_revision: str | None = "0005_sql_audits"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create feedback and follow-up suggestion tables."""
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("thread_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["query_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thread_id"], ["query_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_mirrors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_feedbacks_public_id"),
        sa.UniqueConstraint("run_id", "user_id", name="uq_feedbacks_run_user"),
    )
    op.create_index("ix_feedbacks_user_created", "feedbacks", ["user_id", "created_at"])
    op.create_index("ix_feedbacks_run", "feedbacks", ["run_id"])

    op.create_table(
        "followup_suggestions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=True),
        sa.Column("thread_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("suggestion_text", sa.String(length=500), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["query_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thread_id"], ["query_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_mirrors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_followup_suggestions_public_id"),
    )
    op.create_index(
        "ix_followup_suggestions_run_rank",
        "followup_suggestions",
        ["run_id", "rank"],
    )
    op.create_index(
        "ix_followup_suggestions_thread_rank",
        "followup_suggestions",
        ["thread_id", "rank"],
    )
    op.create_index(
        "ix_followup_suggestions_user_created",
        "followup_suggestions",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    """Drop feedback and follow-up suggestion tables."""
    op.drop_index("ix_followup_suggestions_user_created", table_name="followup_suggestions")
    op.drop_index("ix_followup_suggestions_thread_rank", table_name="followup_suggestions")
    op.drop_index("ix_followup_suggestions_run_rank", table_name="followup_suggestions")
    op.drop_table("followup_suggestions")
    op.drop_index("ix_feedbacks_run", table_name="feedbacks")
    op.drop_index("ix_feedbacks_user_created", table_name="feedbacks")
    op.drop_table("feedbacks")
