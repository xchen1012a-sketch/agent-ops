"""Domain error types and unified error envelope.

Errors are raised by application/domain layers and mapped to HTTP responses
by the error handlers in api/dependencies.py. They carry stable error codes
that surface to clients and audit logs.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all expected domain errors."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500
    retryable: bool = False

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthError(AppError):
    code = "AUTH_REQUIRED"
    http_status = 401


class ForbiddenError(AppError):
    code = "AUTH_FORBIDDEN"
    http_status = 403


class RateLimitedError(AppError):
    code = "RATE_LIMITED"
    http_status = 429
    retryable = True


class InputBlockedError(AppError):
    code = "INPUT_BLOCKED"
    http_status = 422


class LLMTimeoutError(AppError):
    code = "LLM_TIMEOUT"
    http_status = 504
    retryable = True


class RetrievalFailedError(AppError):
    code = "RETRIEVAL_FAILED"
    http_status = 503
    retryable = True


class DBUnavailableError(AppError):
    code = "DB_UNAVAILABLE"
    http_status = 503
    retryable = True


def build_error_envelope(
    request_id: str,
    code: str,
    message: str,
    *,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the unified JSON error envelope returned to clients."""
    return {
        "request_id": request_id,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "details": details or {},
        },
    }
