"""Baseline evaluation harness tests for the data-query agent."""

from __future__ import annotations

import pytest

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.application.services.evaluation_service import DataQueryEvaluationService
from data_query_agent.infrastructure.db.fake_query_adapter import (
    FakeReadOnlyQueryAdapter,
    make_query_result,
)


@pytest.mark.asyncio
async def test_eight_standard_questions_run_in_fake_adapter_mode() -> None:
    catalog_service = DataCatalogService()
    fixtures = catalog_service.load_evaluation_fixtures().fixtures
    adapter = FakeReadOnlyQueryAdapter(
        {
            fixture.baseline_sql: make_query_result(
                columns=fixture.expected_result.columns,
                rows=fixture.expected_result.rows,
                truncated=fixture.expected_result.truncated,
            )
            for fixture in fixtures
        }
    )

    result = await DataQueryEvaluationService(catalog_service).run_baseline_suite(
        query_adapter=adapter
    )

    assert result.version == "v1"
    assert result.total_cases == 8
    assert result.passed_cases == 8
    assert result.failed_cases == 0
    assert result.passed is True
    assert {case.case_id for case in result.results} == {
        "T1",
        "T2",
        "T3",
        "T4",
        "T5",
        "T6",
        "T7",
        "T8",
    }


@pytest.mark.asyncio
async def test_baseline_evaluation_reports_unregistered_sql_failure() -> None:
    result = await DataQueryEvaluationService().run_baseline_suite(
        query_adapter=FakeReadOnlyQueryAdapter()
    )

    assert result.total_cases == 8
    assert result.passed is False
    assert result.failed_cases == 8
    assert {case.error_code for case in result.results} == {"sql_not_registered"}
