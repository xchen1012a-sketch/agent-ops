"""Fake read-only query adapter for deterministic tests and workflow slices."""

from __future__ import annotations

import json

from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionErrorCode,
    QueryExecutionRequest,
    QueryExecutionResult,
)


class FakeReadOnlyQueryAdapter:
    """In-memory query adapter that never opens a real database connection."""

    def __init__(
        self,
        fixtures: dict[str, QueryExecutionResult] | None = None,
        failures: dict[str, QueryExecutionErrorCode] | None = None,
    ) -> None:
        self._fixtures = {_normalize_sql(sql): result for sql, result in (fixtures or {}).items()}
        self._failures = {_normalize_sql(sql): code for sql, code in (failures or {}).items()}

    async def execute(self, request: QueryExecutionRequest) -> QueryExecutionResult:
        """Return a fixture result or mapped safe adapter error."""
        sql_key = _normalize_sql(request.sql)
        failure_code = self._failures.get(sql_key)
        if failure_code is not None:
            raise QueryExecutionError(failure_code, _message_for_error(failure_code))
        result = self._fixtures.get(sql_key)
        if result is None:
            raise QueryExecutionError(
                QueryExecutionErrorCode.SQL_NOT_REGISTERED,
                "SQL fixture is not registered in fake query adapter",
            )
        _validate_result_limits(result, request)
        return result


def make_query_result(
    *,
    columns: tuple[str, ...],
    rows: tuple[tuple[object, ...], ...],
    truncated: bool = False,
) -> QueryExecutionResult:
    """Create a structured query result with computed resource usage."""
    return QueryExecutionResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        field_count=len(columns),
        byte_count=_estimate_result_bytes(columns, rows),
        truncated=truncated,
    )


def _validate_result_limits(
    result: QueryExecutionResult,
    request: QueryExecutionRequest,
) -> None:
    if result.row_count > request.max_rows:
        raise QueryExecutionError(
            QueryExecutionErrorCode.RESULT_TOO_LARGE,
            "Query result exceeds max rows",
        )
    if result.field_count > request.max_fields:
        raise QueryExecutionError(
            QueryExecutionErrorCode.RESULT_TOO_LARGE,
            "Query result exceeds max fields",
        )
    if result.byte_count > request.max_bytes:
        raise QueryExecutionError(
            QueryExecutionErrorCode.RESULT_TOO_LARGE,
            "Query result exceeds max bytes",
        )


def _message_for_error(code: QueryExecutionErrorCode) -> str:
    return {
        QueryExecutionErrorCode.TIMEOUT: "Query execution timed out",
        QueryExecutionErrorCode.CONNECTION_FAILED: "Query database connection failed",
        QueryExecutionErrorCode.RESULT_TOO_LARGE: "Query result is too large",
        QueryExecutionErrorCode.SQL_NOT_REGISTERED: "SQL fixture is not registered",
    }[code]


def _estimate_result_bytes(columns: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> int:
    payload = {"columns": columns, "rows": rows}
    return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split())
