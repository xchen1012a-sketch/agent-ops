"""Add query runs and node runs.

Revision ID: 0004_query_runs_node_runs
Revises: 0003_thread_messages
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_query_runs_node_runs"
down_revision: str | None = "0003_thread_messages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create query run and node trace tables."""
    op.create_table(
        "query_runs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("thread_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("question_message_id", sa.BigInteger(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["query_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_mirrors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["question_message_id"],
            ["thread_messages.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_query_runs_public_id"),
    )
    op.create_index(
        "ix_query_runs_thread_created",
        "query_runs",
        ["thread_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_query_runs_user_status_created",
        "query_runs",
        ["user_id", "status", "created_at"],
        unique=False,
    )

    op.create_table(
        "node_runs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("node_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["query_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_node_runs_public_id"),
    )
    op.create_index(
        "ix_node_runs_run_created",
        "node_runs",
        ["run_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_node_runs_run_node_attempt",
        "node_runs",
        ["run_id", "node_name", "attempt"],
        unique=False,
    )


def downgrade() -> None:
    """Drop node trace and query run tables."""
    op.drop_index("ix_node_runs_run_node_attempt", table_name="node_runs")
    op.drop_index("ix_node_runs_run_created", table_name="node_runs")
    op.drop_table("node_runs")
    op.drop_index("ix_query_runs_user_status_created", table_name="query_runs")
    op.drop_index("ix_query_runs_thread_created", table_name="query_runs")
    op.drop_table("query_runs")
