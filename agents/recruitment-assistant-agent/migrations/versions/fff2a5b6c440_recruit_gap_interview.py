"""recruit gap and interview layer

Revision ID: fff2a5b6c440
Revises: eee1f4a5b330
Create Date: 2026-07-05 17:00:00.000000

Hand-written because no local MySQL was available for autogenerate in this
slice. The recruitment Agent's RECRUIT-230 fifth batch introduces 2 tables:
``gap_analyses``, ``interview_questions``. Real DB upgrade/downgrade is
recorded as "未验证" until a local MySQL run is performed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "fff2a5b6c440"
down_revision: str | None = "eee1f4a5b330"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # gap_analyses depends on match_results.
    op.create_table(
        "gap_analyses",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("match_result_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("gap_description", sa.Text(), nullable=False),
        sa.Column("suggested_question", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["match_result_id"],
            ["match_results.id"],
            name="fk_gap_match",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_gap_analyses_match",
        "gap_analyses",
        ["match_result_id"],
        unique=False,
    )

    # interview_questions depends on match_results.
    op.create_table(
        "interview_questions",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("match_result_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "skill_verification",
                "experience_probe",
                "behavioral",
                "gap_probe",
                name="question_category",
            ),
            nullable=False,
        ),
        sa.Column(
            "difficulty",
            sa.Enum("easy", "medium", "hard", name="question_difficulty"),
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
            name="fk_q_match",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_interview_questions_match",
        "interview_questions",
        ["match_result_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse FK order: interview_questions -> gap_analyses.
    op.drop_index(
        "idx_interview_questions_match",
        table_name="interview_questions",
    )
    op.drop_table("interview_questions")

    op.drop_index("idx_gap_analyses_match", table_name="gap_analyses")
    op.drop_table("gap_analyses")
