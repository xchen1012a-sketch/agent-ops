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
    assert script_dir.get_heads() == ["0005_sql_audits"]


def test_baseline_has_no_down_revision() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    baseline = script_dir.get_revision("0001_initial_baseline")
    assert baseline is not None
    assert baseline.down_revision is None


def test_baseline_migration_file_exists() -> None:
    files = {f.stem for f in (MIGRATIONS_DIR / "versions").glob("*.py")}
    assert "0001_initial_baseline" in files


def test_walk_revisions_returns_exactly_one() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    revisions = list(script_dir.walk_revisions())
    assert [revision.revision for revision in revisions] == [
        "0005_sql_audits",
        "0004_query_runs_node_runs",
        "0003_thread_messages",
        "0002_identity_threads",
        "0001_initial_baseline",
    ]


def test_identity_threads_revision_follows_baseline() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    identity_revision = script_dir.get_revision("0002_identity_threads")
    assert identity_revision is not None
    assert identity_revision.down_revision == "0001_initial_baseline"


def test_thread_messages_revision_follows_identity_threads() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    message_revision = script_dir.get_revision("0003_thread_messages")
    assert message_revision is not None
    assert message_revision.down_revision == "0002_identity_threads"


def test_query_runs_revision_follows_thread_messages() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    run_revision = script_dir.get_revision("0004_query_runs_node_runs")
    assert run_revision is not None
    assert run_revision.down_revision == "0003_thread_messages"


def test_sql_audits_revision_follows_query_runs() -> None:
    script_dir = ScriptDirectory.from_config(_make_config())
    audit_revision = script_dir.get_revision("0005_sql_audits")
    assert audit_revision is not None
    assert audit_revision.down_revision == "0004_query_runs_node_runs"
