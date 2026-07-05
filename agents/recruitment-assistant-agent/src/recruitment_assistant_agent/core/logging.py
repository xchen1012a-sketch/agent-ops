"""Structured logging via loguru with sensitive field scrubbing."""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from recruitment_assistant_agent.core.config import Settings

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "api_key",
        "secret",
        "jwt",
        "deepseek_api_key",
        "database_url",
        "connection_string",
    }
)


def _scrub(record: dict[str, Any]) -> None:
    extra = record.get("extra", {})
    for key in list(extra):
        if key.lower() in SENSITIVE_KEYS:
            extra[key] = "***"


def configure_logging(settings: Settings) -> None:
    """Configure loguru sink based on settings."""
    logger.remove()

    if settings.log_format == "json":
        fmt = (
            '{{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
            '"level":"{level}",'
            '"service":"{extra[service]}",'
            '"env":"{extra[env]}",'
            '"message":"{message}",'
            '"extra":{_extra}}}'
        )
    else:
        fmt = "{time:HH:mm:ss.SSS} {level:<7} {name}:{line} {message}"

    logger.configure(
        extra={"service": settings.app_name, "env": settings.app_env},
        patcher=_scrub,  # type: ignore[arg-type]  # loguru Record is a dict alias; stubs are stricter than runtime
    )

    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=fmt,
        backtrace=False,
        diagnose=False,
        enqueue=True,
    )


def get_logger(name: str) -> Any:
    """Return a logger bound with the module name."""
    return logger.bind(module=name)
