"""SQL AST safety validation for generated data-query SQL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import cast

import sqlglot
from sqlglot import exp

from data_query_agent.domain.policies.sql_whitelist import SqlPolicyConfig, SqlWhitelistSource


class SqlPolicyViolationCode(StrEnum):
    """Stable violation codes emitted by the SQL policy boundary."""

    PARSE_ERROR = "parse_error"
    MULTIPLE_STATEMENTS = "multiple_statements"
    COMMENT_NOT_ALLOWED = "comment_not_allowed"
    NON_SELECT_STATEMENT = "non_select_statement"
    UNION_NOT_ALLOWED = "union_not_allowed"
    FORBIDDEN_CLAUSE = "forbidden_clause"
    FORBIDDEN_KEYWORD = "forbidden_keyword"
    SYSTEM_SCHEMA_NOT_ALLOWED = "system_schema_not_allowed"
    TABLE_NOT_ALLOWED = "table_not_allowed"
    COLUMN_NOT_ALLOWED = "column_not_allowed"
    FUNCTION_NOT_ALLOWED = "function_not_allowed"
    LIMIT_REQUIRED = "limit_required"
    LIMIT_TOO_LARGE = "limit_too_large"
    FIELD_COUNT_TOO_LARGE = "field_count_too_large"
    RESULT_ROW_COUNT_TOO_LARGE = "result_row_count_too_large"
    RESULT_FIELD_COUNT_TOO_LARGE = "result_field_count_too_large"
    RESULT_BYTES_TOO_LARGE = "result_bytes_too_large"


@dataclass(frozen=True, slots=True)
class QueryResultResourceUsage:
    """Observed result resource usage after query execution."""

    row_count: int
    field_count: int
    byte_count: int


@dataclass(frozen=True, slots=True)
class SqlPolicyViolation:
    """One SQL policy violation with a stable code and safe message."""

    code: SqlPolicyViolationCode
    message: str


@dataclass(frozen=True, slots=True)
class SqlAstValidationResult:
    """Result of SQL AST validation."""

    is_allowed: bool
    normalized_sql: str | None
    violations: tuple[SqlPolicyViolation, ...]

    @property
    def first_violation(self) -> SqlPolicyViolation | None:
        """Return the first violation when validation failed."""
        return self.violations[0] if self.violations else None


class SqlAstPolicyValidator:
    """Validate generated SQL with sqlglot before any execution boundary."""

    def __init__(
        self,
        policy: SqlPolicyConfig | None = None,
        whitelist: SqlWhitelistSource | None = None,
    ) -> None:
        if policy is not None:
            self._policy = policy
        elif whitelist is not None:
            self._policy = whitelist.policy
        else:
            self._policy = SqlPolicyConfig()
        self._whitelist = whitelist

    def validate(self, sql: str) -> SqlAstValidationResult:
        """Validate that SQL is a single safe SELECT statement."""
        stripped_sql = sql.strip()
        precheck_violation = self._precheck(stripped_sql)
        if precheck_violation is not None:
            return _blocked(precheck_violation)

        try:
            expressions = sqlglot.parse(stripped_sql, read="mysql")
        except sqlglot.errors.SqlglotError:
            return _blocked(
                SqlPolicyViolation(
                    code=SqlPolicyViolationCode.PARSE_ERROR,
                    message="SQL could not be parsed",
                )
            )

        if len(expressions) != self._policy.limits.statement_count:
            return _blocked(
                SqlPolicyViolation(
                    code=SqlPolicyViolationCode.MULTIPLE_STATEMENTS,
                    message="SQL must contain exactly one statement",
                )
            )

        parsed_expression = expressions[0]
        if parsed_expression is None:
            return _blocked(
                SqlPolicyViolation(
                    code=SqlPolicyViolationCode.PARSE_ERROR,
                    message="SQL could not be parsed",
                )
            )
        expression = cast(exp.Expression, parsed_expression)
        ast_violation = self._validate_expression(expression)
        if ast_violation is not None:
            return _blocked(ast_violation)

        return SqlAstValidationResult(
            is_allowed=True,
            normalized_sql=expression.sql(dialect="mysql"),
            violations=(),
        )

    def validate_result_resources(
        self,
        usage: QueryResultResourceUsage,
    ) -> SqlAstValidationResult:
        """Validate observed query result resource usage."""
        limits = self._policy.limits
        if usage.row_count > limits.max_rows:
            return _blocked(
                SqlPolicyViolation(
                    code=SqlPolicyViolationCode.RESULT_ROW_COUNT_TOO_LARGE,
                    message="Query result row count exceeds policy limit",
                )
            )
        if usage.field_count > limits.max_fields:
            return _blocked(
                SqlPolicyViolation(
                    code=SqlPolicyViolationCode.RESULT_FIELD_COUNT_TOO_LARGE,
                    message="Query result field count exceeds policy limit",
                )
            )
        if usage.byte_count > limits.max_bytes:
            return _blocked(
                SqlPolicyViolation(
                    code=SqlPolicyViolationCode.RESULT_BYTES_TOO_LARGE,
                    message="Query result byte size exceeds policy limit",
                )
            )
        return SqlAstValidationResult(is_allowed=True, normalized_sql=None, violations=())

    def _precheck(self, sql: str) -> SqlPolicyViolation | None:
        if _contains_comment(sql):
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.COMMENT_NOT_ALLOWED,
                message="SQL comments are not allowed",
            )
        if _contains_multiple_statement_separator(sql):
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.MULTIPLE_STATEMENTS,
                message="Multiple SQL statements are not allowed",
            )
        upper_sql = sql.upper()
        for clause in self._policy.forbidden_clauses:
            if _contains_token(upper_sql, clause):
                return SqlPolicyViolation(
                    code=SqlPolicyViolationCode.FORBIDDEN_CLAUSE,
                    message=f"Forbidden SQL clause: {clause}",
                )
        for keyword in self._policy.forbidden_keywords:
            if _contains_token(upper_sql, keyword):
                return SqlPolicyViolation(
                    code=SqlPolicyViolationCode.FORBIDDEN_KEYWORD,
                    message=f"Forbidden SQL keyword: {keyword}",
                )
        return None

    def _validate_expression(self, expression: exp.Expression) -> SqlPolicyViolation | None:
        if isinstance(expression, exp.Union) or any(expression.find_all(exp.Union)):
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.UNION_NOT_ALLOWED,
                message="UNION queries are not allowed",
            )
        if not isinstance(expression, exp.Select):
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.NON_SELECT_STATEMENT,
                message="Only SELECT statements are allowed",
            )

        system_schema_violation = self._validate_system_schema(expression)
        if system_schema_violation is not None:
            return system_schema_violation
        if self._whitelist is None:
            return None
        return self._validate_whitelist(expression)

    def _validate_system_schema(self, expression: exp.Expression) -> SqlPolicyViolation | None:
        for table in expression.find_all(exp.Table):
            schema_name = (table.db or table.catalog or "").upper()
            if schema_name in _SYSTEM_SCHEMAS:
                return SqlPolicyViolation(
                    code=SqlPolicyViolationCode.SYSTEM_SCHEMA_NOT_ALLOWED,
                    message="System schemas are not allowed",
                )
        return None

    def _validate_whitelist(self, expression: exp.Select) -> SqlPolicyViolation | None:
        assert self._whitelist is not None
        table_aliases: dict[str, str] = {}
        query_tables: set[str] = set()
        for table in expression.find_all(exp.Table):
            table_name = table.name
            if not self._whitelist.is_table_allowed(table_name):
                return SqlPolicyViolation(
                    code=SqlPolicyViolationCode.TABLE_NOT_ALLOWED,
                    message=f"Table is not allowed: {table_name}",
                )
            query_tables.add(table_name)
            if table.alias:
                table_aliases[table.alias] = table_name

        if any(expression.find_all(exp.Star)):
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.COLUMN_NOT_ALLOWED,
                message="Wildcard SELECT is not allowed",
            )

        for column in expression.find_all(exp.Column):
            column_table_name = _resolve_column_table(column, query_tables, table_aliases)
            if column_table_name is None or not self._whitelist.is_column_allowed(
                column_table_name, column.name
            ):
                return SqlPolicyViolation(
                    code=SqlPolicyViolationCode.COLUMN_NOT_ALLOWED,
                    message=f"Column is not allowed: {column.sql(dialect='mysql')}",
                )

        for function_name in _iter_function_names(expression):
            if not self._whitelist.is_function_allowed(function_name):
                return SqlPolicyViolation(
                    code=SqlPolicyViolationCode.FUNCTION_NOT_ALLOWED,
                    message=f"Function is not allowed: {function_name}",
                )

        if len(expression.expressions) > self._policy.limits.max_fields:
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.FIELD_COUNT_TOO_LARGE,
                message="Selected field count exceeds policy limit",
            )

        return self._validate_limit(expression)

    def _validate_limit(self, expression: exp.Select) -> SqlPolicyViolation | None:
        limit_expression = expression.args.get("limit")
        if limit_expression is None:
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.LIMIT_REQUIRED,
                message="SELECT statements must include a LIMIT clause",
            )
        if not isinstance(limit_expression, exp.Limit):
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.LIMIT_REQUIRED,
                message="SELECT LIMIT clause is invalid",
            )
        literal = limit_expression.expression
        if not isinstance(literal, exp.Literal) or literal.is_string:
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.LIMIT_REQUIRED,
                message="SELECT LIMIT must be a numeric literal",
            )
        try:
            limit_value = int(str(literal.this))
        except ValueError:
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.LIMIT_REQUIRED,
                message="SELECT LIMIT must be a numeric literal",
            )
        if limit_value > self._policy.limits.max_rows:
            return SqlPolicyViolation(
                code=SqlPolicyViolationCode.LIMIT_TOO_LARGE,
                message="SELECT LIMIT exceeds policy max rows",
            )
        return None


_SYSTEM_SCHEMAS = frozenset({"INFORMATION_SCHEMA", "MYSQL", "PERFORMANCE_SCHEMA", "SYS"})
_FUNCTION_NAME_ALIASES = {
    "TIME_TO_STR": "DATE_FORMAT",
    "TS_OR_DS_TO_DATE": "DATE",
    "TS_OR_DS_TO_TIMESTAMP": "DATE",
}


def _resolve_column_table(
    column: exp.Column,
    query_tables: set[str],
    table_aliases: dict[str, str],
) -> str | None:
    if column.table:
        return table_aliases.get(column.table, column.table)
    if len(query_tables) == 1:
        return next(iter(query_tables))
    return None


def _iter_function_names(expression: exp.Expression) -> tuple[str, ...]:
    names: list[str] = []
    for function in expression.find_all(exp.Func):
        if isinstance(function, exp.And | exp.Or):
            continue
        function_name = function.name or type(function).__name__
        normalized = _FUNCTION_NAME_ALIASES.get(_to_sql_function_name(function_name), function_name)
        names.append(normalized.upper())
    return tuple(names)


def _to_sql_function_name(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.upper())
    return "".join(chars)


def _contains_comment(sql: str) -> bool:
    return "--" in sql or "/*" in sql or "*/" in sql or "#" in sql


def _contains_multiple_statement_separator(sql: str) -> bool:
    return ";" in sql.rstrip(";")


def _contains_token(upper_sql: str, token: str) -> bool:
    normalized_token = token.upper()
    if " " in normalized_token:
        return normalized_token in upper_sql
    return any(part == normalized_token for part in _split_non_word(upper_sql))


def _split_non_word(value: str) -> tuple[str, ...]:
    token = ""
    tokens: list[str] = []
    for char in value:
        if char.isalnum() or char == "_":
            token += char
        elif token:
            tokens.append(token)
            token = ""
    if token:
        tokens.append(token)
    return tuple(tokens)


def _blocked(violation: SqlPolicyViolation) -> SqlAstValidationResult:
    return SqlAstValidationResult(
        is_allowed=False,
        normalized_sql=None,
        violations=(violation,),
    )
