"""Read-only SQLAlchemy query adapter for the shop_db business database.

Implements ``ReadOnlyQueryAdapter`` against ``SHOP_DB_READ_URL`` using
``sqlalchemy.ext.asyncio`` + ``asyncmy``. The adapter is defence-in-depth:
even though ``SqlAstPolicyValidator`` has already verified the statement, we
still set the transaction read-only, apply a server-side timeout, and cap
result resources before returning structured rows.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, TimeoutError as SATimeoutError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionErrorCode,
    QueryExecutionRequest,
    QueryExecutionResult,
)


class _SyncEngineFactory(Protocol):
    """Indirection used by tests to inject a fake engine."""

    def __call__(self, url: str) -> AsyncEngine: ...


@dataclass(frozen=True, slots=True)
class _AdapterLimits:
    max_rows: int
    max_fields: int
    max_bytes: int


class SqlAlchemyReadOnlyQueryAdapter:
    """Read-only SELECT execution against the configured business database.

    The adapter owns its own engine so the agent's read-write database pool is
    not affected. Engines are cached per-URL so repeated requests reuse the
    underlying connection pool.
    """

    def __init__(
        self,
        *,
        read_url: str,
        engine_factory: _SyncEngineFactory | None = None,
        engines: dict[str, AsyncEngine] | None = None,
    ) -> None:
        if not read_url:
            raise QueryExecutionError(
                QueryExecutionErrorCode.CONNECTION_FAILED,
                "SHOP_DB_READ_URL is not configured",
            )
        self._read_url = read_url
        self._engine_factory = engine_factory or _default_engine_factory
        # Engines are shared across requests but cached per-URL. Tests may inject
        # a private dict to isolate one adapter from another.
        self._engines = engines if engines is not None else _GLOBAL_ENGINES

    async def execute(self, request: QueryExecutionRequest) -> QueryExecutionResult:
        """Execute a single read-only SELECT and return a structured result."""
        sql = request.sql.strip()
        if not sql:
            raise QueryExecutionError(
                QueryExecutionErrorCode.SQL_NOT_REGISTERED,
                "empty SQL submitted to query adapter",
            )

        engine = self._get_engine()
        limits = _AdapterLimits(
            max_rows=request.max_rows,
            max_fields=request.max_fields,
            max_bytes=request.max_bytes,
        )
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
                result = await conn.execute(
                    text(sql),
                    execution_options={"timeout": float(request.timeout_seconds)},
                )
                cursor = result.cursor
                field_names = tuple(cursor.description or ())
                column_names = _column_names(field_names)
                _enforce_field_limit(column_names, limits)
                rows: list[tuple[object, ...]] = []
                byte_total = 0
                truncated = False
                for row in result.fetchall():
                    if len(rows) >= limits.max_rows:
                        truncated = True
                        break
                    values = tuple(_normalize(cell) for cell in row)
                    byte_total += _estimate_row_bytes(column_names, values)
                    if byte_total > limits.max_bytes:
                        raise QueryExecutionError(
                            QueryExecutionErrorCode.RESULT_TOO_LARGE,
                            "query result byte size exceeds configured limit",
                        )
                    rows.append(values)
        except SATimeoutError as exc:
            raise QueryExecutionError(
                QueryExecutionErrorCode.TIMEOUT,
                "query execution timed out",
            ) from exc
        except OperationalError as exc:
            code = (
                QueryExecutionErrorCode.TIMEOUT
                if "timeout" in str(exc).lower()
                else QueryExecutionErrorCode.CONNECTION_FAILED
            )
            raise QueryExecutionError(code, "query execution failed") from exc
        except DBAPIError as exc:
            raise QueryExecutionError(
                QueryExecutionErrorCode.CONNECTION_FAILED,
                "database error during query execution",
            ) from exc

        return QueryExecutionResult(
            columns=column_names,
            rows=tuple(rows),
            row_count=len(rows),
            field_count=len(column_names),
            byte_count=byte_total,
            truncated=truncated,
        )

    def _get_engine(self) -> AsyncEngine:
        engine = self._engines.get(self._read_url)
        if engine is None:
            engine = self._engine_factory(self._read_url)
            self._engines[self._read_url] = engine
        return engine


_GLOBAL_ENGINES: dict[str, AsyncEngine] = {}


def _default_engine_factory(url: str) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_pre_ping=True,
        future=True,
    )


def _column_names(description: Any) -> tuple[str, ...]:
    if not description:
        return ()
    names: list[str] = []
    for col in description:
        if isinstance(col, Mapping):
            name = col.get("name") or ""
        elif isinstance(col, (tuple, list)) and col:
            name = str(col[0])
        else:
            name = str(col)
        names.append(name)
    return tuple(names)


def _enforce_field_limit(columns: tuple[str, ...], limits: _AdapterLimits) -> None:
    if len(columns) > limits.max_fields:
        raise QueryExecutionError(
            QueryExecutionErrorCode.RESULT_TOO_LARGE,
            "query result field count exceeds configured limit",
        )


def _normalize(value: object) -> object:
    """Coerce driver-returned scalars into JSON-safe Python primitives."""
    if isinstance(value, Decimal):
        # Preserve numeric precision as a string so the SSE layer never has to
        # worry about float rounding; downstream consumers can parse as needed.
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value


def _estimate_row_bytes(columns: tuple[str, ...], values: tuple[object, ...]) -> int:
    payload = {"columns": columns, "row": values}
    return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))
