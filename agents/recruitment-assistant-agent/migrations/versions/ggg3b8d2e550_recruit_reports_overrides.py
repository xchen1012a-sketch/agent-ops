"""recruit reports and manual overrides layer

Revision ID: ggg3b8d2e550
Revises: fff2a5b6c440
Create Date: 2026-07-05 18:00:00.000000

Hand-written because no local MySQL was available for autogenerate in this
slice. The recruitment Agent's RECRUIT-230 sixth batch introduces 2 tables:
``reports``, ``manual_overrides``. Real DB upgrade/downgrade is
recorded as "未验证" until a local MySQL run is performed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "ggg3b8d2e550"
down_revision: str | None = "fff2a5b6c440"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # reports depends on tasks, match_results, and users (creator).
    op.create_table(
        "reports",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", mysql.CHAR(36), nullable=False),
        sa.Column("task_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("match_result_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("pdf_path", sa.String(length=255), nullable=True),
        sa.Column("created_by", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("expires_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_reports_task",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["match_result_id"],
            ["match_results.id"],
            name="fk_reports_match",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_reports_creator",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uk_reports_public_id"),
    )
    op.create_index(
        "idx_reports_task",
        "reports",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "idx_reports_match",
        "reports",
        ["match_result_id"],
        unique=False,
    )
    op.create_index(
        "idx_reports_expires",
        "reports",
        ["expires_at"],
        unique=False,
    )

    # manual_overrides depends on match_results and users (admin).
    op.create_table(
        "manual_overrides",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("match_result_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("field_path", sa.String(length=255), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("admin_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["match_result_id"],
            ["match_results.id"],
            name="fk_override_match",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["users.id"],
            name="fk_override_admin",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_manual_overrides_match",
        "manual_overrides",
        ["match_result_id"],
        unique=False,
    )
    op.create_index(
        "idx_manual_overrides_admin",
        "manual_overrides",
        ["admin_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse FK order: manual_overrides -> reports.
    op.drop_index(
        "idx_manual_overrides_admin",
        table_name="manual_overrides",
    )
    op.drop_index(
        "idx_manual_overrides_match",
        table_name="manual_overrides",
    )
    op.drop_table("manual_overrides")

    op.drop_index("idx_reports_expires", table_name="reports")
    op.drop_index("idx_reports_match", table_name="reports")
    op.drop_index("idx_reports_task", table_name="reports")
    op.drop_table("reports")
