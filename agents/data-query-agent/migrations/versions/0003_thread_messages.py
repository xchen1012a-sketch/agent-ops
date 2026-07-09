"""Add thread messages.

Revision ID: 0003_thread_messages
Revises: 0002_identity_threads
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_thread_messages"
down_revision: str | None = "0002_identity_threads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create thread message table."""
    op.create_table(
        "thread_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("thread_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.String(length=4000), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["query_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_mirrors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_thread_messages_public_id"),
    )
    op.create_index(
        "ix_thread_messages_thread_created",
        "thread_messages",
        ["thread_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_thread_messages_user_created",
        "thread_messages",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop thread message table."""
    op.drop_index("ix_thread_messages_user_created", table_name="thread_messages")
    op.drop_index("ix_thread_messages_thread_created", table_name="thread_messages")
    op.drop_table("thread_messages")
