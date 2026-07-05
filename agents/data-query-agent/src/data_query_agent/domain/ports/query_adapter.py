"""Port for read-only SQL query execution adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class QueryExecutionErrorCode(StrEnum):
    """Stable query execution error codes returned by adapters."""

    TIMEOUT = "timeout"
    CONNECTION_FAILED = "connection_failed"
    RESULT_TOO_LARGE = "result_too_large"
    SQL_NOT_REGISTERED = "sql_not_registered"


class QueryExecutionError(RuntimeError):
    """Safe adapter error raised without leaking driver internals."""

    def __init__(self, code: QueryExecutionErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class QueryExecutionRequest:
    """Read-only SQL execution request."""

    sql: str
    timeout_seconds: int
    max_rows: int
    max_fields: int
    max_bytes: int


@dataclass(frozen=True, slots=True)
class QueryExecutionResult:
    """Structured table result returned by a query adapter."""

    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    row_count: int
    field_count: int
    byte_count: int
    truncated: bool = False


class ReadOnlyQueryAdapter(Protocol):
    """Boundary for read-only SQL execution."""

    async def execute(self, request: QueryExecutionRequest) -> QueryExecutionResult:
        """Execute a validated read-only SQL query."""
