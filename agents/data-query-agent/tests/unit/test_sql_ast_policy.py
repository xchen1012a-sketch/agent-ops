"""Unit tests for SQL AST safety validation."""

from __future__ import annotations

import pytest

from data_query_agent.domain.policies.sql_ast import (
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
