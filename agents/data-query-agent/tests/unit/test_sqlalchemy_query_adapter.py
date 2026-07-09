"""Unit tests for the SQLAlchemy read-only query adapter.

The real adapter touches ``SHOP_DB_READ_URL`` via ``create_async_engine``, which
we cannot exercise in unit tests. Instead we inject a fake engine factory that
returns scripted responses, and we verify the adapter correctly:
  * normalises rows and columns into structured results
  * enforces max_rows truncation
  * enforces max_fields and max_bytes limits
  * maps SQLAlchemy OperationalError / TimeoutError / DBAPIError to the stable
    QueryExecutionErrorCode enum
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy.exc import DBAPIError, OperationalError, TimeoutError as SATimeoutError
from sqlalchemy.ext.asyncio import AsyncEngine

from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionErrorCode,
    QueryExecutionRequest,
)
from data_query_agent.infrastructure.db.sqlalchemy_query_adapter import (
    SqlAlchemyReadOnlyQueryAdapter,
)


def _request(
    sql: str,
    *,
    max_rows: int = 100,
    max_fields: int = 20,
    max_bytes: int = 65_536,
    timeout_seconds: int = 10,
) -> QueryExecutionRequest:
    return QueryExecutionRequest(
        sql=sql,
        timeout_seconds=timeout_seconds,
        max_rows=max_rows,
        max_fields=max_fields,
        max_bytes=max_bytes,
    )


class _FakeCursor:
    def __init__(self, description: list[tuple[str, ...]]) -> None:
        self.description = description


class _FakeResult:
    def __init__(self, columns: list[str], rows: list[tuple[Any, ...]]) -> None:
        self.cursor = _FakeCursor([(name,) for name in columns])
        self._rows = rows

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._rows)


class _FakeConnection:
    """Minimal async connection that scripts execute() responses."""

    def __init__(self, *, scripted: dict[str, Any] | None = None) -> None:
        self._scripted = scripted or {}
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    async def execute(self, statement: Any, execution_options: dict[str, Any] | None = None) -> Any:
        sql_text = str(statement)
        self.calls.append((sql_text, execution_options))
        if sql_text == "SET SESSION TRANSACTION READ ONLY":
            return None
        response = self._scripted.get(sql_text)
        if isinstance(response, Exception):
            raise response
        return response

    async def __aenter__(self) -> _FakeConnection:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class _FakeEngine:
    """Engine double that yields a single scripted connection."""

    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection

    def connect(self) -> _FakeConnection:
        return self._connection


def _build_adapter(
    *,
    scripted: dict[str, Any],
    read_url: str = "mysql+asyncmy://reader:x@127.0.0.1:13306/shop_db",
) -> tuple[SqlAlchemyReadOnlyQueryAdapter, _FakeConnection]:
    connection = _FakeConnection(scripted=scripted)
    engines: dict[str, AsyncEngine] = {}

    def factory(url: str) -> AsyncEngine:
        engines[url] = _FakeEngine(connection)  # type: ignore[assignment]
        return engines[url]  # type: ignore[return-value]

    adapter = SqlAlchemyReadOnlyQueryAdapter(
        read_url=read_url,
        engine_factory=factory,
        engines=engines,
    )
    return adapter, connection


@pytest.mark.asyncio
async def test_adapter_executes_select_and_returns_structured_result() -> None:
    sql = "SELECT region, total_sales FROM wide_orders LIMIT 5"
    adapter, connection = _build_adapter(
        scripted={
            sql: _FakeResult(
                columns=["region", "total_sales"],
                rows=[("East", 1000), ("West", 800)],
            )
        }
    )

    result = await adapter.execute(_request(sql))

    assert result.columns == ("region", "total_sales")
    assert result.rows == (("East", 1000.0), ("West", 800.0))
    assert result.row_count == 2
    assert result.field_count == 2
    assert result.byte_count > 0
    assert result.truncated is False
    # Ensure read-only guard is the first statement issued.
    assert connection.calls[0][0] == "SET SESSION TRANSACTION READ ONLY"


@pytest.mark.asyncio
async def test_adapter_truncates_when_result_exceeds_max_rows() -> None:
    sql = "SELECT id FROM wide_orders LIMIT 100"
    adapter, _ = _build_adapter(
        scripted={sql: _FakeResult(columns=["id"], rows=[(i,) for i in range(5)])}
    )

    result = await adapter.execute(_request(sql, max_rows=2))

    assert result.row_count == 2
    assert result.truncated is True


@pytest.mark.asyncio
async def test_adapter_raises_result_too_large_when_field_count_exceeds_limit() -> None:
    sql = "SELECT a, b, c, d FROM wide_orders LIMIT 1"
    adapter, _ = _build_adapter(
        scripted={
            sql: _FakeResult(
                columns=["a", "b", "c", "d"],
                rows=[(1, 2, 3, 4)],
            )
        }
    )

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request(sql, max_fields=3))

    assert exc_info.value.code is QueryExecutionErrorCode.RESULT_TOO_LARGE


@pytest.mark.asyncio
async def test_adapter_raises_result_too_large_when_byte_budget_exceeded() -> None:
    sql = "SELECT payload FROM wide_orders LIMIT 5"
    adapter, _ = _build_adapter(
        scripted={
            sql: _FakeResult(
                columns=["payload"],
                rows=[("x" * 200,) for _ in range(5)],
            )
        }
    )

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request(sql, max_bytes=200))

    assert exc_info.value.code is QueryExecutionErrorCode.RESULT_TOO_LARGE


@pytest.mark.asyncio
async def test_adapter_maps_timeout_error() -> None:
    sql = "SELECT slow FROM wide_orders LIMIT 1"
    adapter, _ = _build_adapter(scripted={sql: SATimeoutError()})

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request(sql))

    assert exc_info.value.code is QueryExecutionErrorCode.TIMEOUT


@pytest.mark.asyncio
async def test_adapter_maps_operational_error_with_timeout_keyword_to_timeout() -> None:
    sql = "SELECT slow FROM wide_orders LIMIT 1"
    adapter, _ = _build_adapter(
        scripted={
            sql: OperationalError(
                statement=sql,
                params=None,
                orig=Exception("Lock wait timeout exceeded"),
            )
        }
    )

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request(sql))

    assert exc_info.value.code is QueryExecutionErrorCode.TIMEOUT


@pytest.mark.asyncio
async def test_adapter_maps_operational_error_to_connection_failed() -> None:
    sql = "SELECT bad FROM wide_orders LIMIT 1"
    adapter, _ = _build_adapter(
        scripted={
            sql: OperationalError(
                statement=sql,
                params=None,
                orig=Exception("Connection refused"),
            )
        }
    )

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request(sql))

    assert exc_info.value.code is QueryExecutionErrorCode.CONNECTION_FAILED


@pytest.mark.asyncio
async def test_adapter_maps_generic_dbapi_error_to_connection_failed() -> None:
    sql = "SELECT risky FROM wide_orders LIMIT 1"
    adapter, _ = _build_adapter(
        scripted={
            sql: DBAPIError(
                statement=sql,
                params=None,
                orig=Exception("unknown"),
            )
        }
    )

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request(sql))

    assert exc_info.value.code is QueryExecutionErrorCode.CONNECTION_FAILED


@pytest.mark.asyncio
async def test_adapter_requires_read_url() -> None:
    with pytest.raises(QueryExecutionError) as exc_info:
        SqlAlchemyReadOnlyQueryAdapter(
            read_url="",
            engine_factory=lambda url: _FakeEngine(_FakeConnection()),  # type: ignore[arg-type]
            engines={},
        )

    assert exc_info.value.code is QueryExecutionErrorCode.CONNECTION_FAILED


@pytest.mark.asyncio
async def test_adapter_rejects_empty_sql() -> None:
    adapter, _ = _build_adapter(scripted={})

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request("   "))

    assert exc_info.value.code is QueryExecutionErrorCode.SQL_NOT_REGISTERED


def test_normalize_converts_decimal_to_float_for_json_safety() -> None:
    from data_query_agent.infrastructure.db.sqlalchemy_query_adapter import (
        _estimate_row_bytes,
        _normalize,
    )

    normalized = _normalize(Decimal("12.34"))
    assert isinstance(normalized, float)
    assert normalized == pytest.approx(12.34)
    payload_bytes = _estimate_row_bytes(("amount",), (normalized,))
    assert payload_bytes > 0
