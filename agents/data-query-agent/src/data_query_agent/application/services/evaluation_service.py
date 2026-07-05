"""Evaluation harness for baseline data-query fixtures."""

from __future__ import annotations

from dataclasses import dataclass

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionRequest,
    QueryExecutionResult,
    ReadOnlyQueryAdapter,
)
from data_query_agent.domain.value_objects.data_catalog import EvaluationFixture

BASELINE_EVALUATION_CASE_COUNT = 8


@dataclass(frozen=True, slots=True)
class EvaluationCaseResult:
    """Outcome for one baseline evaluation fixture."""

    case_id: str
    question: str
    verifies: str
    baseline_sql: str
    passed: bool
    row_count: int | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationSuiteResult:
    """Aggregated baseline evaluation suite result."""

    version: str
    results: tuple[EvaluationCaseResult, ...]

    @property
    def total_cases(self) -> int:
        """Return total evaluated cases."""
        return len(self.results)

    @property
    def passed_cases(self) -> int:
        """Return count of passed cases."""
        return sum(1 for result in self.results if result.passed)

    @property
    def failed_cases(self) -> int:
        """Return count of failed cases."""
        return self.total_cases - self.passed_cases

    @property
    def passed(self) -> bool:
        """Return whether all cases passed."""
        return self.failed_cases == 0


class DataQueryEvaluationService:
    """Run deterministic baseline fixtures against a read-only query adapter."""

    def __init__(self, catalog_service: DataCatalogService | None = None) -> None:
        self._catalog_service = catalog_service or DataCatalogService()

    async def run_baseline_suite(
        self,
        *,
        query_adapter: ReadOnlyQueryAdapter,
    ) -> EvaluationSuiteResult:
        """Run the fixed eight-question baseline suite in fake-adapter mode."""
        catalog = self._catalog_service.load_evaluation_fixtures()
        if len(catalog.fixtures) != BASELINE_EVALUATION_CASE_COUNT:
            raise ValueError("baseline evaluation suite must contain exactly 8 fixtures")
        results = []
        for fixture in catalog.fixtures:
            results.append(await self._run_fixture(query_adapter=query_adapter, fixture=fixture))
        return EvaluationSuiteResult(version=catalog.version, results=tuple(results))

    async def _run_fixture(
        self,
        *,
        query_adapter: ReadOnlyQueryAdapter,
        fixture: EvaluationFixture,
    ) -> EvaluationCaseResult:
        limits = self._catalog_service.load_sql_whitelist().policy.limits
        try:
            actual = await query_adapter.execute(
                QueryExecutionRequest(
                    sql=fixture.baseline_sql,
                    timeout_seconds=limits.timeout_seconds,
                    max_rows=limits.max_rows,
                    max_fields=limits.max_fields,
                    max_bytes=limits.max_bytes,
                )
            )
        except QueryExecutionError as exc:
            return EvaluationCaseResult(
                case_id=fixture.case_id,
                question=fixture.question,
                verifies=fixture.verifies,
                baseline_sql=fixture.baseline_sql,
                passed=False,
                error_code=exc.code.value,
                error_message=exc.message,
            )
        passed = _matches_expected_result(fixture=fixture, actual=actual)
        return EvaluationCaseResult(
            case_id=fixture.case_id,
            question=fixture.question,
            verifies=fixture.verifies,
            baseline_sql=fixture.baseline_sql,
            passed=passed,
            row_count=actual.row_count,
            error_code=None if passed else "RESULT_MISMATCH",
            error_message=None
            if passed
            else "actual result does not match fixture expected_result",
        )


def _matches_expected_result(*, fixture: EvaluationFixture, actual: QueryExecutionResult) -> bool:
    expected = fixture.expected_result
    return (
        actual.columns == expected.columns
        and actual.rows == expected.rows
        and actual.truncated is expected.truncated
    )
