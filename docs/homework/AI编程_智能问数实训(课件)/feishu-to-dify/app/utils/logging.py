"""Loguru logging configuration."""

from __future__ import annotations

import logging
import sys

from loguru import logger

_CONFIGURED = False

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[name]}</cyan> | "
    "<level>{message}</level>"
)


class InterceptHandler(logging.Handler):
    """Route stdlib logging (uvicorn, etc.) through loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).bind(name=record.name).log(
            level, record.getMessage()
        )


def setup_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = level.upper()
    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format=LOG_FORMAT,
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )

    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        std_logger = logging.getLogger(name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False

    _CONFIGURED = True


def get_logger(name: str):
    return logger.bind(name=name)


logger.configure(extra={"name": "app"})

__all__ = ["logger", "get_logger", "setup_logging"]
