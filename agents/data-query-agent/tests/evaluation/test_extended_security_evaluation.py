"""Extended question and SQL security evaluation tests."""

from __future__ import annotations

import pytest

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.application.services.evaluation_service import DataQueryEvaluationService
from data_query_agent.infrastructure.db.fake_query_adapter import (
    FakeReadOnlyQueryAdapter,
    make_query_result,
)


def _adapter_for_extended_fixtures() -> FakeReadOnlyQueryAdapter:
    fixtures = DataCatalogService().load_extended_evaluation_fixtures().fixtures
    return FakeReadOnlyQueryAdapter(
        {
            fixture.baseline_sql: make_query_result(
                columns=fixture.expected_result.columns,
                rows=fixture.expected_result.rows,
                truncated=fixture.expected_result.truncated,
            )
            for fixture in fixtures
        }
    )


@pytest.mark.asyncio
async def test_extended_thirty_question_suite_runs_in_fake_adapter_mode() -> None:
    result = await DataQueryEvaluationService().run_extended_suite(
        query_adapter=_adapter_for_extended_fixtures()
    )

    assert result.version == "v1"
    assert result.total_cases == 30
    assert result.passed_cases == 30
    assert result.failed_cases == 0
    assert result.passed is True
    assert {case.case_id for case in result.results} == {f"E{index:02d}" for index in range(1, 31)}


def test_security_attack_suite_blocks_all_attack_fixtures() -> None:
    result = DataQueryEvaluationService().run_security_attack_suite()

    assert result.version == "v1"
    assert result.total_cases == 10
    assert result.blocked_cases == 10
    assert result.passed_cases == 10
    assert result.passed is True
    assert all(case.actual_violation == case.expected_violation for case in result.results)


def test_catalog_loads_extended_and_security_fixture_sources() -> None:
    service = DataCatalogService()

    extended = service.load_extended_evaluation_fixtures()
    attacks = service.load_security_attack_fixtures()

    assert len(extended.fixtures) == 30
    assert len(attacks.fixtures) == 10
    assert all(fixture.expected_result.columns for fixture in extended.fixtures)
    assert all(fixture.expected_violation for fixture in attacks.fixtures)
