"""SQL AST safety validation for generated data-query SQL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import cast

import sqlglot
from sqlglot import exp

from data_query_agent.domain.policies.sql_whitelist import SqlPolicyConfig


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

    def __init__(self, policy: SqlPolicyConfig | None = None) -> None:
        self._policy = policy or SqlPolicyConfig()

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
        for table in expression.find_all(exp.Table):
            schema_name = (table.db or table.catalog or "").upper()
            if schema_name in _SYSTEM_SCHEMAS:
                return SqlPolicyViolation(
                    code=SqlPolicyViolationCode.SYSTEM_SCHEMA_NOT_ALLOWED,
                    message="System schemas are not allowed",
                )
        return None


_SYSTEM_SCHEMAS = frozenset({"INFORMATION_SCHEMA", "MYSQL", "PERFORMANCE_SCHEMA", "SYS"})


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
