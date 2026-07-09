"""recruit match results layer

Revision ID: eee1f4a5b330
Revises: ddd9e1f3a220
Create Date: 2026-07-05 16:00:00.000000

Hand-written because no local MySQL was available for autogenerate in this
slice. The recruitment Agent's RECRUIT-230 fourth batch introduces 2 tables:
``match_results``, ``match_items``. Real DB upgrade/downgrade is recorded as
"未验证" until a local MySQL run is performed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "eee1f4a5b330"
down_revision: str | None = "ddd9e1f3a220"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # match_results depends on tasks.
    op.create_table(
        "match_results",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("task_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("resume_structure_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("jd_structure_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("skill_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("experience_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("education_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("soft_skill_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("overall_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "tier",
            sa.Enum("match", "partial", "no_evidence", name="match_tier"),
            nullable=False,
        ),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("rule_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_match_task",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resume_structure_id",
            "jd_structure_id",
            name="uk_match_pair",
        ),
    )
    op.create_index(
        "idx_match_results_task",
        "match_results",
        ["task_id"],
        unique=False,
    )

    # match_items depends on match_results.
    op.create_table(
        "match_items",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("match_result_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("requirement", sa.String(length=255), nullable=False),
        sa.Column(
            "match_status",
            sa.Enum("match", "partial", "no_evidence", name="match_status"),
            nullable=False,
        ),
        sa.Column("evidence_snippet", sa.Text(), nullable=True),
        sa.Column(
            "skill_category",
            sa.Enum(
                "skill",
                "experience",
                "education",
                "certification",
                "soft_skill",
                name="skill_category",
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["match_result_id"],
            ["match_results.id"],
            name="fk_item_match",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_match_items_result",
        "match_items",
        ["match_result_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse FK order: match_items -> match_results.
    op.drop_index("idx_match_items_result", table_name="match_items")
    op.drop_table("match_items")

    op.drop_index("idx_match_results_task", table_name="match_results")
    op.drop_table("match_results")
