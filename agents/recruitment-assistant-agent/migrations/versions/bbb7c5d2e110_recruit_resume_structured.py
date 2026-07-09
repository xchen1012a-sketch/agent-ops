"""recruit resume structured layer

Revision ID: bbb7c5d2e110
Revises: ccc46fb6a333
Create Date: 2026-07-05 14:00:00.000000

Hand-written because no local MySQL was available for autogenerate in this
slice. The recruitment Agent's RECRUIT-230 second batch introduces 4 tables:
``resume_structures``, ``skill_evidence``, ``experience_evidence``,
``education_evidence``. Real DB upgrade/downgrade is recorded as "未验证"
until a local MySQL run is performed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "bbb7c5d2e110"
down_revision: str | None = "ccc46fb6a333"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # resume_structures depends on tasks and materials.
    op.create_table(
        "resume_structures",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("task_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("material_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "total_years_exp",
            sa.Numeric(precision=5, scale=1),
            nullable=True,
        ),
        sa.Column("raw_structured", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_resume_structures_task",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["material_id"],
            ["materials.id"],
            name="fk_resume_structures_material",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "material_id",
            "version",
            name="uq_resume_structures_material_version",
        ),
    )
    op.create_index(
        "idx_resume_structures_material_version",
        "resume_structures",
        ["material_id", "version"],
        unique=False,
    )

    # skill_evidence depends on resume_structures.
    op.create_table(
        "skill_evidence",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("resume_structure_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("skill_name", sa.String(length=100), nullable=False),
        sa.Column("evidence_snippet", sa.Text(), nullable=False),
        sa.Column("source_section", sa.String(length=100), nullable=True),
        sa.Column(
            "proficiency",
            sa.Enum(
                "beginner",
                "intermediate",
                "advanced",
                "expert",
                name="proficiency",
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
            ["resume_structure_id"],
            ["resume_structures.id"],
            name="fk_skill_evidence_structure",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_skill_evidence_structure",
        "skill_evidence",
        ["resume_structure_id"],
        unique=False,
    )

    # experience_evidence depends on resume_structures.
    op.create_table(
        "experience_evidence",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("resume_structure_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("role_title", sa.String(length=100), nullable=False),
        sa.Column("company_redacted", sa.String(length=100), nullable=True),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("evidence_snippet", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["resume_structure_id"],
            ["resume_structures.id"],
            name="fk_experience_evidence_structure",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_experience_evidence_structure",
        "experience_evidence",
        ["resume_structure_id"],
        unique=False,
    )

    # education_evidence depends on resume_structures.
    op.create_table(
        "education_evidence",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("resume_structure_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "degree",
            sa.Enum(
                "high_school",
                "associate",
                "bachelor",
                "master",
                "phd",
                "other",
                name="degree",
            ),
            nullable=True,
        ),
        sa.Column("major", sa.String(length=100), nullable=True),
        sa.Column(
            "school_tier",
            sa.Enum(
                "tier1",
                "tier2",
                "tier3",
                "overseas",
                "other",
                name="school_tier",
            ),
            nullable=True,
        ),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("evidence_snippet", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["resume_structure_id"],
            ["resume_structures.id"],
            name="fk_education_evidence_structure",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_education_evidence_structure",
        "education_evidence",
        ["resume_structure_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse FK order: education → experience → skill → resume_structures.
    op.drop_index(
        "idx_education_evidence_structure",
        table_name="education_evidence",
    )
    op.drop_table("education_evidence")

    op.drop_index(
        "idx_experience_evidence_structure",
        table_name="experience_evidence",
    )
    op.drop_table("experience_evidence")

    op.drop_index("idx_skill_evidence_structure", table_name="skill_evidence")
    op.drop_table("skill_evidence")

    op.drop_index(
        "idx_resume_structures_material_version",
        table_name="resume_structures",
    )
    op.drop_table("resume_structures")
