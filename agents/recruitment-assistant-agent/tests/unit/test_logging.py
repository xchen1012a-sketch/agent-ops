"""Unit tests for structured logging configuration and sensitive field scrubbing."""

from __future__ import annotations

from loguru import logger

from recruitment_assistant_agent.core.config import Settings
from recruitment_assistant_agent.core.logging import (
    SENSITIVE_KEYS,
    _scrub,
    configure_logging,
    get_logger,
)


def _make_settings(log_format: str = "json") -> Settings:
    return Settings(
        jwt_secret="x" * 32,
        database_url="mysql+asyncmy://u:p@mysql:3306/db",
        deepseek_api_key="sk-test",
        log_format=log_format,  # type: ignore[arg-type]
    )


def test_scrub_redacts_sensitive_keys() -> None:
    record = {"extra": {"password": "secret", "user_id": 42}}
    _scrub(record)
    assert record["extra"]["password"] == "***"
    assert record["extra"]["user_id"] == 42


def test_scrub_handles_missing_extra() -> None:
    record: dict[str, object] = {}
    _scrub(record)


def test_scrub_is_case_insensitive() -> None:
    assert "PASSWORD" not in SENSITIVE_KEYS
    record = {"extra": {"PASSWORD": "x"}}
    _scrub(record)
    assert record["extra"]["PASSWORD"] == "***"


def test_configure_logging_json_format_does_not_raise() -> None:
    configure_logging(_make_settings(log_format="json"))


def test_configure_logging_text_format_does_not_raise() -> None:
    configure_logging(_make_settings(log_format="text"))


def test_get_logger_returns_bound_logger() -> None:
    log = get_logger("test_module")
    assert log is not None
    assert callable(logger.bind)
