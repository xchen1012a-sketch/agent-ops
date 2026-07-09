"""recruit jd structured layer

Revision ID: ddd9e1f3a220
Revises: bbb7c5d2e110
Create Date: 2026-07-05 15:00:00.000000

Hand-written because no local MySQL was available for autogenerate in this
slice. The recruitment Agent's RECRUIT-230 third batch introduces 2 tables:
``jd_structures``, ``jd_requirements``. Real DB upgrade/downgrade is recorded
as "未验证" until a local MySQL run is performed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "ddd9e1f3a220"
down_revision: str | None = "bbb7c5d2e110"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # jd_structures depends on tasks and materials.
    op.create_table(
        "jd_structures",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("task_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("material_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("job_title", sa.String(length=200), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
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
            name="fk_jd_structures_task",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["material_id"],
            ["materials.id"],
            name="fk_jd_structures_material",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "material_id",
            "version",
            name="uq_jd_structures_material_version",
        ),
    )
    op.create_index(
        "idx_jd_structures_material_version",
        "jd_structures",
        ["material_id", "version"],
        unique=False,
    )

    # jd_requirements depends on jd_structures.
    op.create_table(
        "jd_requirements",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("jd_structure_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "requirement_type",
            sa.Enum("must_have", "nice_to_have", name="requirement_type"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "weight_hint",
            sa.Numeric(precision=3, scale=2),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["jd_structure_id"],
            ["jd_structures.id"],
            name="fk_jd_requirements_structure",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_jd_requirements_structure",
        "jd_requirements",
        ["jd_structure_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse FK order: jd_requirements -> jd_structures.
    op.drop_index(
        "idx_jd_requirements_structure",
        table_name="jd_requirements",
    )
    op.drop_table("jd_requirements")

    op.drop_index(
        "idx_jd_structures_material_version",
        table_name="jd_structures",
    )
    op.drop_table("jd_structures")
