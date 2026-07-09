"""Unit tests for the Alembic migration chain structure.

These tests verify the migration graph is well-formed (single head, contiguous
chain) without connecting to a real database. Actual upgrade/downgrade against
MySQL is validated in CI via docker-compose (see deployment runbook).
"""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "migrations"


def _make_config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    return cfg


def test_single_head_revision() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    assert script_dir.get_heads() == ["cfg1_user_api_config"]


def test_baseline_has_no_down_revision() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    baseline = script_dir.get_revision("0001_initial_baseline")
    assert baseline is not None
    assert baseline.down_revision is None


def test_baseline_migration_file_exists() -> None:
    files = {f.stem for f in (MIGRATIONS_DIR / "versions").glob("*.py")}
    assert "0001_initial_baseline" in files


def test_walk_revisions_returns_current_chain() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    revisions = list(script_dir.walk_revisions())
    assert [revision.revision for revision in revisions] == [
        "cfg1_user_api_config",
        "ceeb31ed5ac6",
        "d12ac236028f",
        "1644fb1c1451",
        "d85ad25f66ec",
        "a89e7df18324",
        "fcecead92ecd",
        "0001_initial_baseline",
    ]
