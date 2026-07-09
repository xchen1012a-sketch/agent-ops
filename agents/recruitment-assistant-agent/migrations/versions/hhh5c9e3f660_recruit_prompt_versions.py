"""recruit prompt versions layer

Revision ID: hhh5c9e3f660
Revises: ggg3b8d2e550
Create Date: 2026-07-05 19:00:00.000000

Hand-written because no local MySQL was available for autogenerate in this
slice. The recruitment Agent's RECRUIT-230 seventh (and final) batch
introduces 1 table: ``prompt_versions``. Real DB upgrade/downgrade is
recorded as "未验证" until a local MySQL run is performed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "hhh5c9e3f660"
down_revision: str | None = "ggg3b8d2e550"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # prompt_versions depends on users (creator).
    op.create_table(
        "prompt_versions",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", mysql.CHAR(36), nullable=False),
        sa.Column("prompt_name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("template_key", sa.String(length=255), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=True),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "retired", name="prompt_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_by", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_prompt_creator",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prompt_name", "version", name="uk_prompt_name_version"),
    )
    op.create_index(
        "idx_prompt_versions_name_status",
        "prompt_versions",
        ["prompt_name", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_prompt_versions_name_status",
        table_name="prompt_versions",
    )
    op.drop_table("prompt_versions")
