"""Unit tests for the fake read-only query adapter."""

from __future__ import annotations

import pytest

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionErrorCode,
    QueryExecutionRequest,
)
from data_query_agent.infrastructure.db.fake_query_adapter import (
    FakeReadOnlyQueryAdapter,
    make_fixture_query_adapter,
    make_query_result,
)


def _request(
    sql: str, *, max_rows: int = 100, max_fields: int = 20, max_bytes: int = 4096
) -> QueryExecutionRequest:
    return QueryExecutionRequest(
        sql=sql,
        timeout_seconds=10,
        max_rows=max_rows,
        max_fields=max_fields,
        max_bytes=max_bytes,
    )


@pytest.mark.asyncio
async def test_fake_adapter_returns_registered_structured_result() -> None:
    result = make_query_result(
        columns=("region", "total_sales"),
        rows=(("East", 1000), ("West", 800)),
    )
    adapter = FakeReadOnlyQueryAdapter(
        fixtures={"SELECT region, total_sales FROM sales LIMIT 10": result}
    )

    actual = await adapter.execute(_request("  SELECT region, total_sales FROM sales LIMIT 10  "))

    assert actual == result
    assert actual.columns == ("region", "total_sales")
    assert actual.row_count == 2
    assert actual.field_count == 2
    assert actual.byte_count > 0
    assert actual.truncated is False


@pytest.mark.asyncio
async def test_fake_adapter_maps_timeout_and_connection_failed_errors() -> None:
    adapter = FakeReadOnlyQueryAdapter(
        failures={
            "SELECT timeout FROM wide_orders LIMIT 1": QueryExecutionErrorCode.TIMEOUT,
            "SELECT connection FROM wide_orders LIMIT 1": QueryExecutionErrorCode.CONNECTION_FAILED,
        }
    )

    with pytest.raises(QueryExecutionError) as timeout_error:
        await adapter.execute(_request("SELECT timeout FROM wide_orders LIMIT 1"))
    with pytest.raises(QueryExecutionError) as connection_error:
        await adapter.execute(_request("SELECT connection FROM wide_orders LIMIT 1"))

    assert timeout_error.value.code is QueryExecutionErrorCode.TIMEOUT
    assert timeout_error.value.message == "Query execution timed out"
    assert connection_error.value.code is QueryExecutionErrorCode.CONNECTION_FAILED
    assert connection_error.value.message == "Query database connection failed"


@pytest.mark.asyncio
async def test_fake_adapter_rejects_unregistered_sql() -> None:
    adapter = FakeReadOnlyQueryAdapter()

    with pytest.raises(QueryExecutionError) as exc_info:
        await adapter.execute(_request("SELECT 1"))

    assert exc_info.value.code is QueryExecutionErrorCode.SQL_NOT_REGISTERED


@pytest.mark.asyncio
async def test_fake_adapter_maps_result_too_large_by_rows_fields_and_bytes() -> None:
    rows_result = make_query_result(columns=("id",), rows=((1,), (2,)))
    fields_result = make_query_result(columns=("a", "b"), rows=((1, 2),))
    bytes_result = make_query_result(columns=("payload",), rows=(("x" * 200,),))
    adapter = FakeReadOnlyQueryAdapter(
        fixtures={
            "SELECT rows FROM t LIMIT 2": rows_result,
            "SELECT fields FROM t LIMIT 1": fields_result,
            "SELECT bytes FROM t LIMIT 1": bytes_result,
        }
    )

    with pytest.raises(QueryExecutionError) as row_error:
        await adapter.execute(_request("SELECT rows FROM t LIMIT 2", max_rows=1))
    with pytest.raises(QueryExecutionError) as field_error:
        await adapter.execute(_request("SELECT fields FROM t LIMIT 1", max_fields=1))
    with pytest.raises(QueryExecutionError) as bytes_error:
        await adapter.execute(_request("SELECT bytes FROM t LIMIT 1", max_bytes=50))

    assert row_error.value.code is QueryExecutionErrorCode.RESULT_TOO_LARGE
    assert field_error.value.code is QueryExecutionErrorCode.RESULT_TOO_LARGE
    assert bytes_error.value.code is QueryExecutionErrorCode.RESULT_TOO_LARGE


def test_make_query_result_can_mark_truncated_results() -> None:
    result = make_query_result(columns=("id",), rows=((1,),), truncated=True)

    assert result.truncated is True
    assert result.row_count == 1
    assert result.field_count == 1


@pytest.mark.asyncio
async def test_fixture_query_adapter_registers_all_standard_questions() -> None:
    catalog = DataCatalogService().load_evaluation_fixtures()
    adapter = make_fixture_query_adapter(catalog)

    for fixture in catalog.fixtures:
        actual = await adapter.execute(_request(fixture.baseline_sql))

        assert actual.columns == fixture.expected_result.columns
        assert actual.rows == fixture.expected_result.rows
        assert actual.truncated is fixture.expected_result.truncated
