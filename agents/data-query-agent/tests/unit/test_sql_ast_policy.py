"""Unit tests for SQL AST safety validation."""

from __future__ import annotations

import pytest

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.domain.policies.sql_ast import (
    QueryResultResourceUsage,
    SqlAstPolicyValidator,
    SqlPolicyViolationCode,
)


def test_select_statement_is_allowed_and_normalized() -> None:
    result = SqlAstPolicyValidator().validate(
        "select order_id, total_amount from wide_orders where total_amount > 0 limit 10"
    )

    assert result.is_allowed is True
    assert result.violations == ()
    assert result.normalized_sql == (
        "SELECT order_id, total_amount FROM wide_orders WHERE total_amount > 0 LIMIT 10"
    )


@pytest.mark.parametrize(
    ("sql", "code"),
    [
        ("INSERT INTO wide_orders(order_id) VALUES (1)", SqlPolicyViolationCode.FORBIDDEN_CLAUSE),
        ("UPDATE wide_orders SET total_amount = 0", SqlPolicyViolationCode.FORBIDDEN_CLAUSE),
        ("DELETE FROM wide_orders", SqlPolicyViolationCode.FORBIDDEN_CLAUSE),
        ("DROP TABLE wide_orders", SqlPolicyViolationCode.FORBIDDEN_CLAUSE),
        ("ALTER TABLE wide_orders ADD COLUMN x INT", SqlPolicyViolationCode.FORBIDDEN_CLAUSE),
        ("TRUNCATE TABLE wide_orders", SqlPolicyViolationCode.FORBIDDEN_CLAUSE),
    ],
)
def test_write_and_ddl_statements_are_blocked(sql: str, code: SqlPolicyViolationCode) -> None:
    result = SqlAstPolicyValidator().validate(sql)

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is code


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM wide_orders; SELECT * FROM wide_order_details",
        "SELECT * FROM wide_orders; SELECT 1;",
    ],
)
def test_multiple_statements_are_blocked(sql: str) -> None:
    result = SqlAstPolicyValidator().validate(sql)

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.MULTIPLE_STATEMENTS


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM wide_orders -- bypass",
        "SELECT * FROM wide_orders /* bypass */",
        "SELECT * FROM wide_orders # bypass",
    ],
)
def test_comment_bypass_is_blocked(sql: str) -> None:
    result = SqlAstPolicyValidator().validate(sql)

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.COMMENT_NOT_ALLOWED


def test_union_is_blocked() -> None:
    result = SqlAstPolicyValidator().validate(
        "SELECT order_id FROM wide_orders UNION SELECT user FROM mysql.user"
    )

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code in {
        SqlPolicyViolationCode.UNION_NOT_ALLOWED,
        SqlPolicyViolationCode.FORBIDDEN_KEYWORD,
    }


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM mysql.user",
        "SELECT * FROM performance_schema.events_statements_current",
        "SELECT * FROM sys.schema_table_statistics",
    ],
)
def test_system_schema_is_blocked(sql: str) -> None:
    result = SqlAstPolicyValidator().validate(sql)

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code in {
        SqlPolicyViolationCode.SYSTEM_SCHEMA_NOT_ALLOWED,
        SqlPolicyViolationCode.FORBIDDEN_KEYWORD,
    }


def test_parse_error_is_blocked() -> None:
    result = SqlAstPolicyValidator().validate("SELECT FROM")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.PARSE_ERROR


def test_with_select_is_allowed_in_basic_ast_slice() -> None:
    result = SqlAstPolicyValidator().validate("WITH sales AS (SELECT 1 AS x) SELECT x FROM sales")

    assert result.is_allowed is True
    assert result.normalized_sql is not None


def _whitelist_validator() -> SqlAstPolicyValidator:
    return SqlAstPolicyValidator(whitelist=DataCatalogService().load_sql_whitelist())


def test_whitelisted_table_column_function_and_limit_are_allowed() -> None:
    result = _whitelist_validator().validate(
        "SELECT SUM(total_amount) AS total FROM wide_orders WHERE region = 'East' LIMIT 100"
    )

    assert result.is_allowed is True
    assert result.normalized_sql is not None


def test_non_whitelisted_table_is_blocked() -> None:
    result = _whitelist_validator().validate("SELECT total_amount FROM not_allowed LIMIT 10")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.TABLE_NOT_ALLOWED


def test_non_whitelisted_column_is_blocked() -> None:
    result = _whitelist_validator().validate("SELECT password FROM wide_orders LIMIT 10")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.COLUMN_NOT_ALLOWED


def test_wildcard_select_is_blocked_by_column_policy() -> None:
    result = _whitelist_validator().validate("SELECT * FROM wide_orders LIMIT 10")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.COLUMN_NOT_ALLOWED


def test_non_whitelisted_function_is_blocked() -> None:
    result = _whitelist_validator().validate("SELECT MD5(customer_id) FROM wide_orders LIMIT 10")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.FUNCTION_NOT_ALLOWED


def test_missing_limit_is_blocked_by_whitelist_policy() -> None:
    result = _whitelist_validator().validate("SELECT order_id FROM wide_orders")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.LIMIT_REQUIRED


def test_limit_above_max_rows_is_blocked() -> None:
    result = _whitelist_validator().validate("SELECT order_id FROM wide_orders LIMIT 1001")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.LIMIT_TOO_LARGE


def test_field_count_above_limit_is_blocked() -> None:
    columns = ", ".join(f"order_id AS order_id_{index}" for index in range(51))
    result = _whitelist_validator().validate(f"SELECT {columns} FROM wide_orders LIMIT 10")

    assert result.is_allowed is False
    assert result.first_violation is not None
    assert result.first_violation.code is SqlPolicyViolationCode.FIELD_COUNT_TOO_LARGE


def test_result_resource_limits_are_checked_after_execution() -> None:
    validator = _whitelist_validator()

    too_many_rows = validator.validate_result_resources(
        QueryResultResourceUsage(row_count=1001, field_count=10, byte_count=1024)
    )
    too_many_fields = validator.validate_result_resources(
        QueryResultResourceUsage(row_count=10, field_count=51, byte_count=1024)
    )
    too_many_bytes = validator.validate_result_resources(
        QueryResultResourceUsage(row_count=10, field_count=10, byte_count=1_048_577)
    )
    allowed = validator.validate_result_resources(
        QueryResultResourceUsage(row_count=10, field_count=10, byte_count=1024)
    )

    assert too_many_rows.first_violation is not None
    assert too_many_rows.first_violation.code is SqlPolicyViolationCode.RESULT_ROW_COUNT_TOO_LARGE
    assert too_many_fields.first_violation is not None
    assert (
        too_many_fields.first_violation.code is SqlPolicyViolationCode.RESULT_FIELD_COUNT_TOO_LARGE
    )
    assert too_many_bytes.first_violation is not None
    assert too_many_bytes.first_violation.code is SqlPolicyViolationCode.RESULT_BYTES_TOO_LARGE
    assert allowed.is_allowed is True
