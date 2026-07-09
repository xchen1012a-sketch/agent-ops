"""recruit identity data layer

Revision ID: ccc46fb6a333
Revises: 0001_initial_baseline
Create Date: 2026-07-05 13:00:00.000000

Hand-written because no local MySQL was available for autogenerate in this
slice. The recruitment Agent's first RECRUIT-230 batch introduces 5 tables:
``users``, ``tasks``, ``materials``, ``agent_runs``, ``node_runs``. Real DB
upgrade/downgrade is recorded as "未验证" until a local MySQL run is performed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "ccc46fb6a333"
down_revision: str | None = "0001_initial_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # agent_runs: no FK dependencies; create first.
    op.create_table(
        "agent_runs",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", mysql.CHAR(length=36), nullable=False),
        sa.Column("thread_id", mysql.CHAR(length=36), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("workflow_version", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "success",
                "failed",
                "retrying",
                "canceled",
                name="run_status",
            ),
            nullable=False,
        ),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("finished_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("idx_runs_status", "agent_runs", ["status"], unique=False)
    op.create_index("idx_runs_thread", "agent_runs", ["thread_id", "started_at"], unique=False)

    # users: no FK dependencies; mirrors unified-auth user identity.
    op.create_table(
        "users",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", mysql.CHAR(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="user_role"),
            server_default="user",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("active", "disabled", name="user_status"),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("public_id"),
    )

    # node_runs: depends on agent_runs.
    op.create_table(
        "node_runs",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("run_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("node_name", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "success",
                "failed",
                "retrying",
                "canceled",
                name="node_run_status",
            ),
            nullable=False,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("started_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("finished_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["agent_runs.id"],
            name="fk_node_run",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_node_runs_run", "node_runs", ["run_id", "started_at"], unique=False)

    # tasks: depends on users.
    op.create_table(
        "tasks",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", mysql.CHAR(length=36), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "uploaded",
                "parsing",
                "parsed",
                "matching",
                "reviewing",
                "completed",
                "failed",
                name="task_status",
            ),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("normal", "urgent", name="task_priority"),
            server_default="normal",
            nullable=False,
        ),
        sa.Column(
            "review_status",
            sa.Enum(
                "pending",
                "approved",
                "rejected",
                "changes_requested",
                name="review_status",
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("reviewed_by", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("reviewed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_tasks_user"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], name="fk_tasks_reviewer"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("idx_tasks_user_time", "tasks", ["user_id", "created_at"], unique=False)
    op.create_index(
        "idx_tasks_review",
        "tasks",
        ["review_status", "created_at"],
        unique=False,
    )

    # materials: depends on tasks.
    op.create_table(
        "materials",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("public_id", mysql.CHAR(length=36), nullable=False),
        sa.Column("task_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("resume", "jd", name="material_kind"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_hash", mysql.CHAR(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column(
            "scan_status",
            sa.Enum("pending", "clean", "infected", "failed", name="scan_status"),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "original_deleted",
            sa.Boolean(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("deleted_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_materials_task",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("idx_materials_hash", "materials", ["file_hash"], unique=False)
    op.create_index("idx_materials_task", "materials", ["task_id"], unique=False)


def downgrade() -> None:
    # Drop in reverse FK order: materials -> tasks -> node_runs -> users -> agent_runs.
    op.drop_index("idx_materials_task", table_name="materials")
    op.drop_index("idx_materials_hash", table_name="materials")
    op.drop_table("materials")

    op.drop_index("idx_tasks_review", table_name="tasks")
    op.drop_index("idx_tasks_user_time", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("idx_node_runs_run", table_name="node_runs")
    op.drop_table("node_runs")

    op.drop_table("users")

    op.drop_index("idx_runs_thread", table_name="agent_runs")
    op.drop_index("idx_runs_status", table_name="agent_runs")
    op.drop_table("agent_runs")
