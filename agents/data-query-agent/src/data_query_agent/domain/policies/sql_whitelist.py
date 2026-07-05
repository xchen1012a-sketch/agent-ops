"""SQL whitelist source models for data-query policy checks."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from data_query_agent.domain.value_objects.data_catalog import CatalogValidationError


class FunctionWhitelist(BaseModel):
    """Allowed SQL function groups."""

    model_config = ConfigDict(frozen=True)

    aggregate: tuple[str, ...] = ()
    date: tuple[str, ...] = ()
    string: tuple[str, ...] = ()
    numeric: tuple[str, ...] = ()
    control: tuple[str, ...] = ()

    @field_validator("aggregate", "date", "string", "numeric", "control")
    @classmethod
    def _function_names_must_be_uppercase(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(function.strip().upper() for function in value)
        if any(not function for function in normalized):
            raise CatalogValidationError("function name must not be blank")
        if len(set(normalized)) != len(normalized):
            raise CatalogValidationError("function names must be unique within one group")
        return normalized

    def all_names(self) -> frozenset[str]:
        """Return all allowed function names."""
        return frozenset(self.aggregate + self.date + self.string + self.numeric + self.control)


class SqlWhitelistSource(BaseModel):
    """Versioned source of allowed SQL tables, columns and functions."""

    model_config = ConfigDict(frozen=True)

    version: str
    allowed_tables: tuple[str, ...] = Field(min_length=1)
    allowed_columns: dict[str, tuple[str, ...]]
    allowed_functions: FunctionWhitelist

    @field_validator("allowed_tables")
    @classmethod
    def _allowed_tables_must_be_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(table.strip() for table in value)
        if any(not table for table in normalized):
            raise CatalogValidationError("allowed table name must not be blank")
        if len(set(normalized)) != len(normalized):
            raise CatalogValidationError("allowed tables must be unique")
        return normalized

    @field_validator("allowed_columns")
    @classmethod
    def _allowed_columns_must_not_be_empty(
        cls, value: dict[str, tuple[str, ...]]
    ) -> dict[str, tuple[str, ...]]:
        normalized: dict[str, tuple[str, ...]] = {}
        for table_name, columns in value.items():
            clean_table_name = table_name.strip()
            clean_columns = tuple(column.strip() for column in columns)
            if not clean_table_name:
                raise CatalogValidationError("allowed column table name must not be blank")
            if not clean_columns or any(not column for column in clean_columns):
                raise CatalogValidationError("allowed columns must not be blank")
            if len(set(clean_columns)) != len(clean_columns):
                raise CatalogValidationError("allowed columns must be unique")
            normalized[clean_table_name] = clean_columns
        return normalized

    @model_validator(mode="after")
    def _columns_must_reference_allowed_tables(self) -> Self:
        unknown_tables = set(self.allowed_columns) - set(self.allowed_tables)
        if unknown_tables:
            raise CatalogValidationError(
                "allowed_columns references unknown tables: " + ", ".join(sorted(unknown_tables))
            )
        if not self.allowed_functions.all_names():
            raise CatalogValidationError("at least one SQL function must be allowed")
        return self

    def is_table_allowed(self, table_name: str) -> bool:
        """Return whether a table is in the whitelist."""
        return table_name in self.allowed_tables

    def is_column_allowed(self, table_name: str, column_name: str) -> bool:
        """Return whether a column is allowed for a table."""
        return column_name in self.allowed_columns.get(table_name, ())

    def is_function_allowed(self, function_name: str) -> bool:
        """Return whether a SQL function is in the whitelist."""
        return function_name.upper() in self.allowed_functions.all_names()
