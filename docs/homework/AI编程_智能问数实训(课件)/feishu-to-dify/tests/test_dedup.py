"""Unit tests for message deduplication."""

from app.utils.dedup import MessageDeduper


def test_try_acquire_only_once() -> None:
    deduper = MessageDeduper(ttl_seconds=60)
    assert deduper.try_acquire("msg-1") is True
    assert deduper.try_acquire("msg-1") is False


def test_is_duplicate_alias() -> None:
    deduper = MessageDeduper(ttl_seconds=60)
    assert deduper.is_duplicate("msg-2") is False
    assert deduper.is_duplicate("msg-2") is True
