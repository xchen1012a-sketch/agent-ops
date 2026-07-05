"""Add user mirrors and query threads.

Revision ID: 0002_identity_threads
Revises: 0001_initial_baseline
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_identity_threads"
down_revision: str | None = "0001_initial_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create user mirror and thread ownership tables."""
    op.create_table(
        "user_mirrors",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("external_subject", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_user_mirrors_public_id"),
    )
    op.create_index(
        "ix_user_mirrors_external_subject",
        "user_mirrors",
        ["external_subject"],
        unique=True,
    )

    op.create_table(
        "query_threads",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_mirrors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_query_threads_public_id"),
    )
    op.create_index(
        "ix_query_threads_user_created",
        "query_threads",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop query thread and user mirror tables."""
    op.drop_index("ix_query_threads_user_created", table_name="query_threads")
    op.drop_table("query_threads")
    op.drop_index("ix_user_mirrors_external_subject", table_name="user_mirrors")
    op.drop_table("user_mirrors")
