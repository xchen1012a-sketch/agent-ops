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
    heads = script_dir.get_heads()
    assert len(heads) == 1
    assert heads[0] == "iii6_user_api_config"


def test_baseline_has_no_down_revision() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    baseline = script_dir.get_revision("0001_initial_baseline")
    assert baseline is not None
    assert baseline.down_revision is None


def test_baseline_migration_file_exists() -> None:
    files = {f.stem for f in (MIGRATIONS_DIR / "versions").glob("*.py")}
    assert "0001_initial_baseline" in files


def test_walk_revisions_is_contiguous_chain() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    revisions = list(script_dir.walk_revisions())
    # walk_revisions yields head-first; assert a single contiguous chain back to base.
    assert len(revisions) == 9
    assert revisions[0].revision == "iii6_user_api_config"
    assert revisions[0].down_revision == "hhh5c9e3f660"
    assert revisions[1].revision == "hhh5c9e3f660"
    assert revisions[1].down_revision == "ggg3b8d2e550"
    assert revisions[2].revision == "ggg3b8d2e550"
    assert revisions[2].down_revision == "fff2a5b6c440"
    assert revisions[3].revision == "fff2a5b6c440"
    assert revisions[3].down_revision == "eee1f4a5b330"
    assert revisions[4].revision == "eee1f4a5b330"
    assert revisions[4].down_revision == "ddd9e1f3a220"
    assert revisions[5].revision == "ddd9e1f3a220"
    assert revisions[5].down_revision == "bbb7c5d2e110"
    assert revisions[6].revision == "bbb7c5d2e110"
    assert revisions[6].down_revision == "ccc46fb6a333"
    assert revisions[7].revision == "ccc46fb6a333"
    assert revisions[7].down_revision == "0001_initial_baseline"
    assert revisions[8].revision == "0001_initial_baseline"
    assert revisions[8].down_revision is None
