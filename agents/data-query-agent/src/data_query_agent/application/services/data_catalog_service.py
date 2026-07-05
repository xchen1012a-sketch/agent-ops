"""Load versioned data-query catalog sources from package resources."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from data_query_agent.domain.policies.sql_whitelist import SqlWhitelistSource
from data_query_agent.domain.value_objects.data_catalog import (
    EvaluationFixtureCatalog,
    IndicatorCatalog,
    SchemaCatalog,
)

RESOURCE_PACKAGE = "data_query_agent.prompts.data_query"


class DataCatalogService:
    """Application service for machine-readable data-query truth sources."""

    def __init__(self, resource_package: str = RESOURCE_PACKAGE) -> None:
        self._resource_package = resource_package

    def load_schema_catalog(self) -> SchemaCatalog:
        """Load the versioned schema catalog."""
        return SchemaCatalog.model_validate(self._load_json("schema_catalog.v1.json"))

    def load_indicator_catalog(self) -> IndicatorCatalog:
        """Load the versioned indicator catalog."""
        return IndicatorCatalog.model_validate(self._load_json("indicators.v1.json"))

    def load_sql_whitelist(self) -> SqlWhitelistSource:
        """Load the versioned SQL whitelist source."""
        return SqlWhitelistSource.model_validate(self._load_json("sql_whitelist.v1.json"))

    def load_evaluation_fixtures(self) -> EvaluationFixtureCatalog:
        """Load baseline evaluation fixtures."""
        return EvaluationFixtureCatalog.model_validate(
            self._load_json("evaluation_fixtures.v1.json")
        )

    def _load_json(self, file_name: str) -> dict[str, Any]:
        resource = resources.files(self._resource_package).joinpath(file_name)
        with resource.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            raise ValueError(f"{file_name} must contain a JSON object")
        return payload
