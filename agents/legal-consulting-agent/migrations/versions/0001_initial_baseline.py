"""FOUND-010 baseline migration for legal-consulting-agent.

Establishes the migration chain without creating any business tables.
Business schemas are added by subsequent migrations per vertical slice
(LEGAL-100 series). Run ``alembic upgrade head`` against the migration
account (DATABASE_MIGRATION_URL) before deploying any feature migration.

Revision ID: 0001_initial_baseline
Revises:
Create Date: 2026-07-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op baseline. The alembic_version table is created automatically."""
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        op.execute(
            sa.text(
                "ALTER DATABASE DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci"
            )
        )


def downgrade() -> None:
    """Reverse of upgrade: nothing to undo beyond the alembic_version row."""
