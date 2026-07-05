"""Application service for running data-query workflow with audit boundaries."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from data_query_agent.application.services.audit_service import SqlAuditService
from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.application.services.run_service import QueryRunTraceService
from data_query_agent.domain.entities.audit import SqlPolicyDecision
from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun
from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionErrorCode,
    QueryExecutionRequest,
    QueryExecutionResult,
    ReadOnlyQueryAdapter,
)
from data_query_agent.workflows.nodes import (
    input_validation_node,
    intent_classify_node,
    interpret_node,
    polite_refusal_node,
    result_validate_node,
    route_after_intent,
    schema_retrieval_node,
    sql_generate_node,
    sql_policy_check_node,
)
from data_query_agent.workflows.state import DataQueryState

SQL_POLICY_VIOLATION = "SQL_POLICY_VIOLATION"
QUERY_TIMEOUT = "QUERY_TIMEOUT"
QUERY_CONNECTION_FAILED = "QUERY_CONNECTION_FAILED"
QUERY_RESULT_TOO_LARGE = "QUERY_RESULT_TOO_LARGE"
QUERY_EXECUTION_FAILED = "QUERY_EXECUTION_FAILED"


@dataclass(frozen=True, slots=True)
class WorkflowRunResult:
    """Result projection for one workflow runner execution."""

    run: QueryRun
    state: DataQueryState
    succeeded: bool
    retryable: bool
    error_code: str | None = None
    error_message: str | None = None


class DataQueryWorkflowRunner:
    """Run deterministic workflow while persisting run/node/audit boundaries."""

    def __init__(
        self,
        *,
        run_trace_service: QueryRunTraceService,
        audit_service: SqlAuditService,
        query_adapter: ReadOnlyQueryAdapter,
        catalog_service: DataCatalogService | None = None,
    ) -> None:
        self._run_trace_service = run_trace_service
        self._audit_service = audit_service
        self._query_adapter = query_adapter
        self._catalog_service = catalog_service or DataCatalogService()

    async def run(self, *, run: QueryRun, question: str) -> WorkflowRunResult:
        """Run workflow and persist success or failure semantics."""
        if run.id is None:
            raise ValueError("persisted query run must have an id")
        current_run = await self._run_trace_service.start_run(run_id=run.id)
        state: DataQueryState = {"question": question}

        try:
            state = await self._run_node(
                current_run, "input_validation", state, input_validation_node
            )
            state = await self._run_node(
                current_run, "intent_classify", state, intent_classify_node
            )
            if route_after_intent(state) == "polite_refusal":
                state = await self._run_node(
                    current_run, "polite_refusal", state, polite_refusal_node
                )
                current_run = await self._run_trace_service.complete_run(run_id=run.id)
                return WorkflowRunResult(
                    run=current_run,
                    state=state,
                    succeeded=True,
                    retryable=False,
                )

            state = await self._run_node(
                current_run, "schema_retrieval", state, schema_retrieval_node
            )
            state = await self._run_node(current_run, "sql_generate", state, sql_generate_node)
            state = await self._run_node(
                current_run, "sql_policy_check", state, sql_policy_check_node
            )
            if not state.get("policy_allowed", False):
                state = await self._persist_audit_node(
                    current_run, state, SqlPolicyDecision.BLOCKED
                )
                current_run = await self._run_trace_service.fail_run(
                    run_id=run.id,
                    error_code=SQL_POLICY_VIOLATION,
                    error_message="SQL policy blocked generated query",
                )
                return WorkflowRunResult(
                    run=current_run,
                    state=state,
                    succeeded=False,
                    retryable=False,
                    error_code=SQL_POLICY_VIOLATION,
                    error_message="SQL policy blocked generated query",
                )

            state = await self._execute_query_node(current_run, state)
            state = await self._run_node(
                current_run, "result_validate", state, result_validate_node
            )
            state = await self._run_node(current_run, "interpret", state, interpret_node)
            state = await self._persist_audit_node(current_run, state, SqlPolicyDecision.ALLOWED)
            current_run = await self._run_trace_service.complete_run(run_id=run.id)
            return WorkflowRunResult(
                run=current_run,
                state=state,
                succeeded=True,
                retryable=False,
            )
        except QueryExecutionError as exc:
            retryable = exc.code in {
                QueryExecutionErrorCode.TIMEOUT,
                QueryExecutionErrorCode.CONNECTION_FAILED,
            }
            error_code = _map_query_error_code(exc.code)
            state = await self._persist_audit_node(
                current_run, state, SqlPolicyDecision.ALLOWED, exc.message
            )
            current_run = await self._run_trace_service.fail_run(
                run_id=run.id,
                error_code=error_code,
                error_message=exc.message,
            )
            return WorkflowRunResult(
                run=current_run,
                state=state,
                succeeded=False,
                retryable=retryable,
                error_code=error_code,
                error_message=exc.message,
            )

    async def _run_node(
        self,
        run: QueryRun,
        node_name: str,
        state: DataQueryState,
        node: Callable[[DataQueryState], DataQueryState],
    ) -> DataQueryState:
        node_run = await self._start_node(run, node_name)
        try:
            next_state = node(state)
        except Exception as exc:
            await self._run_trace_service.finish_node(
                node_run_id=_require_node_id(node_run),
                status=NodeStatus.FAILED,
                error_code=QUERY_EXECUTION_FAILED,
                error_message=str(exc),
            )
            raise
        await self._run_trace_service.finish_node(
            node_run_id=_require_node_id(node_run),
            status=NodeStatus.SUCCESS,
        )
        return next_state

    async def _execute_query_node(self, run: QueryRun, state: DataQueryState) -> DataQueryState:
        node_run = await self._start_node(run, "query_execute")
        try:
            limits = self._catalog_service.load_sql_whitelist().policy.limits
            result = await self._query_adapter.execute(
                QueryExecutionRequest(
                    sql=state.get("generated_sql", ""),
                    timeout_seconds=limits.timeout_seconds,
                    max_rows=limits.max_rows,
                    max_fields=limits.max_fields,
                    max_bytes=limits.max_bytes,
                )
            )
        except QueryExecutionError as exc:
            await self._run_trace_service.finish_node(
                node_run_id=_require_node_id(node_run),
                status=NodeStatus.FAILED,
                error_code=_map_query_error_code(exc.code),
                error_message=exc.message,
            )
            raise
        await self._run_trace_service.finish_node(
            node_run_id=_require_node_id(node_run),
            status=NodeStatus.SUCCESS,
        )
        return {**state, "query_result": _query_result_to_state(result)}

    async def _persist_audit_node(
        self,
        run: QueryRun,
        state: DataQueryState,
        decision: SqlPolicyDecision,
        result_summary: str | None = None,
    ) -> DataQueryState:
        node_run = await self._start_node(run, "persist_audit")
        sql = state.get("generated_sql", "")
        query_result = state.get("query_result", {})
        row_count = _extract_row_count(query_result)
        await self._audit_service.record_sql_audit(
            run=run,
            decision=decision,
            sql_fingerprint=_fingerprint_sql(sql),
            generated_sql=sql or None,
            redacted_summary=_redacted_sql_summary(sql),
            policy_summary=state.get("policy_error_code", "allowed"),
            row_count=row_count,
            result_summary=result_summary or _result_summary(query_result),
        )
        await self._run_trace_service.finish_node(
            node_run_id=_require_node_id(node_run),
            status=NodeStatus.SUCCESS,
        )
        return state

    async def _start_node(self, run: QueryRun, node_name: str) -> NodeRun:
        node_run = await self._run_trace_service.create_node_run(run=run, node_name=node_name)
        return await self._run_trace_service.start_node(node_run_id=_require_node_id(node_run))


def _query_result_to_state(result: QueryExecutionResult) -> dict[str, object]:
    return {
        "columns": list(result.columns),
        "rows": [list(row) for row in result.rows],
        "row_count": result.row_count,
        "field_count": result.field_count,
        "byte_count": result.byte_count,
        "truncated": result.truncated,
    }


def _extract_row_count(query_result: object) -> int | None:
    if isinstance(query_result, dict):
        row_count = query_result.get("row_count")
        if isinstance(row_count, int):
            return row_count
    return None


def _result_summary(query_result: object) -> str | None:
    if isinstance(query_result, dict) and query_result:
        return "structured query result"
    return None


def _fingerprint_sql(sql: str) -> str:
    return "sha256:" + hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _redacted_sql_summary(sql: str) -> str:
    return "empty sql" if not sql else "validated generated sql"


def _map_query_error_code(code: QueryExecutionErrorCode) -> str:
    return {
        QueryExecutionErrorCode.TIMEOUT: QUERY_TIMEOUT,
        QueryExecutionErrorCode.CONNECTION_FAILED: QUERY_CONNECTION_FAILED,
        QueryExecutionErrorCode.RESULT_TOO_LARGE: QUERY_RESULT_TOO_LARGE,
        QueryExecutionErrorCode.SQL_NOT_REGISTERED: QUERY_EXECUTION_FAILED,
    }[code]


def _require_node_id(node_run: NodeRun) -> int:
    if node_run.id is None:
        raise ValueError("persisted node run must have an id")
    return node_run.id
