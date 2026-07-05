"""create user scoped agent api config

Revision ID: iii6_user_api_config
Revises: hhh5c9e3f660
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "iii6_user_api_config"
down_revision: str | None = "hhh5c9e3f660"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_api_config",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("user_public_id", sa.String(length=64), nullable=False),
        sa.Column("api_type", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("api_key_hint", sa.String(length=16), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("max_retries", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_public_id",
            "api_type",
            name="uk_agent_api_config_user_type",
        ),
    )
    op.create_index(
        "idx_agent_api_config_user",
        "agent_api_config",
        ["user_public_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_agent_api_config_user", table_name="agent_api_config")
    op.drop_table("agent_api_config")
