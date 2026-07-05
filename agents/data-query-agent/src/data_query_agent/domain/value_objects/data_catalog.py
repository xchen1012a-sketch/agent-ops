"""Versioned data catalog and evaluation fixture value objects."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CatalogValidationError(ValueError):
    """Raised when a versioned data-query catalog source is invalid."""


class TableCatalog(BaseModel):
    """Allowed table and column catalog used before SQL policy validation."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    columns: tuple[str, ...] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def _table_name_must_not_be_blank(cls, value: str) -> str:
        table_name = value.strip()
        if not table_name:
            raise CatalogValidationError("table name must not be blank")
        return table_name

    @field_validator("columns")
    @classmethod
    def _columns_must_be_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(column.strip() for column in value)
        if any(not column for column in normalized):
            raise CatalogValidationError("column name must not be blank")
        if len(set(normalized)) != len(normalized):
            raise CatalogValidationError("table columns must be unique")
        return normalized


class SchemaCatalog(BaseModel):
    """Machine-readable source of allowed analytical tables."""

    model_config = ConfigDict(frozen=True)

    version: str
    tables: tuple[TableCatalog, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _table_names_must_be_unique(self) -> Self:
        names = [table.name for table in self.tables]
        if len(set(names)) != len(names):
            raise CatalogValidationError("schema catalog table names must be unique")
        return self

    def table_names(self) -> frozenset[str]:
        """Return all allowed table names."""
        return frozenset(table.name for table in self.tables)

    def column_names_for(self, table_name: str) -> frozenset[str]:
        """Return allowed columns for one table."""
        for table in self.tables:
            if table.name == table_name:
                return frozenset(table.columns)
        raise CatalogValidationError(f"unknown table: {table_name}")


class IndicatorDefinition(BaseModel):
    """Business indicator definition backed by a versioned source."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    expression: str
    applicable_tables: tuple[str, ...] = Field(min_length=1)

    @field_validator("name", "expression")
    @classmethod
    def _required_text_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise CatalogValidationError("indicator field must not be blank")
        return normalized


class IndicatorCatalog(BaseModel):
    """Machine-readable source of indicator names and SQL expressions."""

    model_config = ConfigDict(frozen=True)

    version: str
    indicators: tuple[IndicatorDefinition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _indicator_names_must_be_unique(self) -> Self:
        names = [indicator.name for indicator in self.indicators]
        if len(set(names)) != len(names):
            raise CatalogValidationError("indicator names must be unique")
        return self


class EvaluationFixture(BaseModel):
    """Baseline question and SQL pair for deterministic evaluation."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    question: str
    baseline_sql: str
    verifies: str

    @field_validator("case_id", "question", "baseline_sql", "verifies")
    @classmethod
    def _fixture_text_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise CatalogValidationError("evaluation fixture field must not be blank")
        return normalized


class EvaluationFixtureCatalog(BaseModel):
    """Machine-readable source of baseline evaluation fixtures."""

    model_config = ConfigDict(frozen=True)

    version: str
    fixtures: tuple[EvaluationFixture, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _fixture_ids_must_be_unique(self) -> Self:
        case_ids = [fixture.case_id for fixture in self.fixtures]
        if len(set(case_ids)) != len(case_ids):
            raise CatalogValidationError("evaluation fixture ids must be unique")
        return self
