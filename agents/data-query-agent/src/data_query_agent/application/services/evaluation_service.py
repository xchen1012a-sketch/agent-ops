"""Evaluation harness for baseline data-query fixtures."""

from __future__ import annotations

from dataclasses import dataclass

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.domain.policies.sql_ast import SqlAstPolicyValidator
from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionRequest,
    QueryExecutionResult,
    ReadOnlyQueryAdapter,
)
from data_query_agent.domain.value_objects.data_catalog import EvaluationFixture

BASELINE_EVALUATION_CASE_COUNT = 8
EXTENDED_EVALUATION_CASE_COUNT = 30


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


@dataclass(frozen=True, slots=True)
class SecurityAttackCaseResult:
    """Outcome for one SQL security attack fixture."""

    case_id: str
    verifies: str
    attack_sql: str
    expected_violation: str
    actual_violation: str | None
    blocked: bool
    passed: bool


@dataclass(frozen=True, slots=True)
class SecurityAttackSuiteResult:
    """Aggregated SQL security attack suite result."""

    version: str
    results: tuple[SecurityAttackCaseResult, ...]

    @property
    def total_cases(self) -> int:
        """Return total evaluated attack cases."""
        return len(self.results)

    @property
    def blocked_cases(self) -> int:
        """Return count of blocked attack cases."""
        return sum(1 for result in self.results if result.blocked)

    @property
    def passed_cases(self) -> int:
        """Return count of correctly blocked attack cases."""
        return sum(1 for result in self.results if result.passed)

    @property
    def passed(self) -> bool:
        """Return whether every attack case was blocked as expected."""
        return self.passed_cases == self.total_cases


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
        return await self._run_query_suite(
            query_adapter=query_adapter,
            version=catalog.version,
            fixtures=catalog.fixtures,
            expected_count=BASELINE_EVALUATION_CASE_COUNT,
            suite_name="baseline evaluation suite",
        )

    async def run_extended_suite(
        self,
        *,
        query_adapter: ReadOnlyQueryAdapter,
    ) -> EvaluationSuiteResult:
        """Run the fixed thirty-question extended suite in fake-adapter mode."""
        catalog = self._catalog_service.load_extended_evaluation_fixtures()
        return await self._run_query_suite(
            query_adapter=query_adapter,
            version=catalog.version,
            fixtures=catalog.fixtures,
            expected_count=EXTENDED_EVALUATION_CASE_COUNT,
            suite_name="extended evaluation suite",
        )

    def run_security_attack_suite(self) -> SecurityAttackSuiteResult:
        """Validate that all SQL attack fixtures are blocked by policy."""
        catalog = self._catalog_service.load_security_attack_fixtures()
        validator = SqlAstPolicyValidator(whitelist=self._catalog_service.load_sql_whitelist())
        results = []
        for fixture in catalog.fixtures:
            validation = validator.validate(fixture.attack_sql)
            actual_violation = (
                validation.first_violation.code.value
                if validation.first_violation is not None
                else None
            )
            blocked = not validation.is_allowed
            results.append(
                SecurityAttackCaseResult(
                    case_id=fixture.case_id,
                    verifies=fixture.verifies,
                    attack_sql=fixture.attack_sql,
                    expected_violation=fixture.expected_violation,
                    actual_violation=actual_violation,
                    blocked=blocked,
                    passed=blocked and actual_violation == fixture.expected_violation,
                )
            )
        return SecurityAttackSuiteResult(version=catalog.version, results=tuple(results))

    async def _run_query_suite(
        self,
        *,
        query_adapter: ReadOnlyQueryAdapter,
        version: str,
        fixtures: tuple[EvaluationFixture, ...],
        expected_count: int,
        suite_name: str,
    ) -> EvaluationSuiteResult:
        if len(fixtures) != expected_count:
            raise ValueError(f"{suite_name} must contain exactly {expected_count} fixtures")
        results = []
        for fixture in fixtures:
            results.append(await self._run_fixture(query_adapter=query_adapter, fixture=fixture))
        return EvaluationSuiteResult(version=version, results=tuple(results))

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
