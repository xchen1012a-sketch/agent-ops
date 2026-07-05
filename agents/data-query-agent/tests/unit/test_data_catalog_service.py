"""Unit tests for data-query catalog source loading."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.domain.policies.sql_whitelist import FunctionWhitelist, SqlWhitelistSource
from data_query_agent.domain.value_objects.data_catalog import SchemaCatalog, TableCatalog


def test_load_schema_catalog_contains_expected_tables_and_columns() -> None:
    service = DataCatalogService()

    catalog = service.load_schema_catalog()

    assert catalog.version == "v1"
    assert "wide_orders" in catalog.table_names()
    assert "wide_order_details" in catalog.table_names()
    assert "total_amount" in catalog.column_names_for("wide_orders")
    assert "holiday_name" in catalog.column_names_for("wide_order_details")


def test_load_indicator_catalog_contains_required_indicators() -> None:
    service = DataCatalogService()

    catalog = service.load_indicator_catalog()

    indicator_names = {indicator.name for indicator in catalog.indicators}
    assert {"total_sales", "refund_rate", "gross_margin"}.issubset(indicator_names)


def test_load_sql_whitelist_rejects_unknown_table_references() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SqlWhitelistSource(
            version="v-test",
            allowed_tables=("wide_orders",),
            allowed_columns={"not_allowed": ("total_amount",)},
            allowed_functions=FunctionWhitelist(aggregate=("SUM",)),
        )

    assert "unknown tables" in str(exc_info.value)


def test_sql_whitelist_checks_table_column_and_function_membership() -> None:
    whitelist = DataCatalogService().load_sql_whitelist()

    assert whitelist.is_table_allowed("wide_orders")
    assert whitelist.is_column_allowed("wide_orders", "total_amount")
    assert whitelist.is_function_allowed("sum")
    assert not whitelist.is_table_allowed("mysql.user")
    assert not whitelist.is_column_allowed("wide_orders", "password")
    assert not whitelist.is_function_allowed("sleep")


def test_schema_catalog_rejects_duplicate_table_names() -> None:
    with pytest.raises(ValidationError) as exc_info:
        SchemaCatalog(
            version="v-test",
            tables=(
                TableCatalog(name="wide_orders", description="one", columns=("order_id",)),
                TableCatalog(name="wide_orders", description="two", columns=("order_id",)),
            ),
        )

    assert "table names must be unique" in str(exc_info.value)


def test_load_evaluation_fixtures_contains_eight_standard_questions() -> None:
    fixtures = DataCatalogService().load_evaluation_fixtures()

    assert fixtures.version == "v1"
    assert len(fixtures.fixtures) == 8
    assert {fixture.case_id for fixture in fixtures.fixtures} == {
        "T1",
        "T2",
        "T3",
        "T4",
        "T5",
        "T6",
        "T7",
        "T8",
    }
    assert all(fixture.baseline_sql.upper().startswith("SELECT") for fixture in fixtures.fixtures)
