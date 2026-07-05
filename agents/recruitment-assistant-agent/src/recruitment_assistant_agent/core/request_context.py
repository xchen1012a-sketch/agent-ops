"""Request-scoped context propagation via contextvars."""

from __future__ import annotations

from contextvars import ContextVar

REQUEST_ID_KEY = "request_id"

_request_context: ContextVar[dict[str, object] | None] = ContextVar(
    "request_context",
    default=None,
)

request_context = _request_context
