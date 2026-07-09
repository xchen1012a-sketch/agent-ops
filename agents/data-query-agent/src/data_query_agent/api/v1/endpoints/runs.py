"""Run creation endpoints for data-query workflow requests."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Sequence
from typing import Any, cast

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from data_query_agent.api.dependencies import (
    ChatLlmAdapterDep,
    CurrentSubjectDep,
    DataCatalogServiceDep,
    IdentityThreadServiceDep,
    PromptTemplateServiceDep,
    QueryAdapterDep,
    QueryRunTraceServiceDep,
    ShopSchemaLoaderDep,
)
from data_query_agent.api.v1.schemas.runs import (
    RunCreateRequest,
    RunDataEnvelope,
    RunDetailEnvelope,
    RunDetailResponse,
    RunLocalDemoEnvelope,
    RunLocalDemoResponse,
    RunResponse,
)
from data_query_agent.application.services.conversation_prompt import with_conversation_history
from data_query_agent.application.services.result_interpretation_service import (
    ResultInterpretationService,
)
from data_query_agent.core.errors import AppError, NotFoundError
from data_query_agent.domain.entities.identity import MessageRole, ThreadMessage
from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus
from data_query_agent.domain.policies.sql_ast import SqlAstPolicyValidator
from data_query_agent.domain.policies.sql_whitelist import SqlWhitelistSource
from data_query_agent.domain.ports.llm_adapter import LlmStreamChunk
from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionError,
    QueryExecutionRequest,
)
from data_query_agent.infrastructure.sse import iter_llm_sse
from data_query_agent.workflows.graph import create_data_query_graph
from data_query_agent.workflows.nodes import (
    input_validation_node,
    intent_classify_node,
    polite_refusal_node,
)
from data_query_agent.workflows.prompt_nodes import PromptBackedWorkflowNodes
from data_query_agent.workflows.state import DataQueryState

_HISTORY_LIMIT = 20
_FALLBACK_ANSWER = "暂时无法给出可靠结论，未执行或未完成真实数据查询。"

router = APIRouter()


@router.post("/threads/{thread_id}/runs", response_model=RunDataEnvelope, status_code=201)
async def create_run(
    thread_id: str,
    payload: RunCreateRequest,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> RunDataEnvelope:
    """Create a pending run and user question message without executing workflow."""
    thread = await identity_service.get_owned_thread(
        thread_public_id=thread_id,
        external_subject=subject,
    )
    if thread is None:
        raise NotFoundError("thread not found")
    message = await identity_service.create_message_for_subject(
        external_subject=subject,
        thread_public_id=thread_id,
        role=MessageRole.USER,
        content=payload.question,
    )
    run = await run_trace_service.create_run_for_thread(
        thread=thread,
        question_message_id=message.id,
    )
    return RunDataEnvelope(
        data=RunResponse.from_entity(
            run=run,
            thread_public_id=thread.public_id,
            question=payload.question,
        )
    )


@router.post("/threads/{thread_id}/runs/local-demo", response_model=RunLocalDemoEnvelope)
async def create_local_demo_run(
    thread_id: str,
    payload: RunCreateRequest,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
) -> RunLocalDemoEnvelope:
    """Execute the local deterministic workflow projection for MVP evidence.

    This endpoint is deliberately named local-demo: it does not call a live
    database, Dify app, or Feishu tenant, and it does not replace the persisted
    async run contract.
    """
    thread = await identity_service.get_owned_thread(
        thread_public_id=thread_id,
        external_subject=subject,
    )
    if thread is None:
        raise NotFoundError("thread not found")
    graph = cast(Any, create_data_query_graph())
    state = cast(dict[str, Any], graph.invoke({"question": payload.question}))
    return RunLocalDemoEnvelope(
        data=RunLocalDemoResponse.from_state(question=payload.question, state=state)
    )


@router.post("/threads/{thread_id}/runs/stream")
async def stream_run_completion(
    thread_id: str,
    payload: RunCreateRequest,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    chat_llm_adapter: ChatLlmAdapterDep,
    prompt_template_service: PromptTemplateServiceDep,
    query_adapter: QueryAdapterDep,
    shop_schema_loader: ShopSchemaLoaderDep,
    data_catalog_service: DataCatalogServiceDep,
) -> StreamingResponse:
    """Stream a live thinking/answer completion for a question as SSE.

    Runs the real NL2SQL → AST/whitelist check → shop_db execution → interpret
    pipeline, then pushes results through the model-agnostic SSE contract.
    Conversation history is folded into the prompt so the model sees prior turns.
    The assistant answer is persisted so subsequent turns can reference it.
    """
    thread = await identity_service.get_owned_thread(
        thread_public_id=thread_id,
        external_subject=subject,
    )
    if thread is None:
        raise NotFoundError("thread not found")

    history = await identity_service.list_messages_for_subject(
        external_subject=subject,
        thread_public_id=thread_id,
        limit=_HISTORY_LIMIT,
    )
    # Persist the user turn first so subsequent turns see [user, assistant, ...]
    # pairs in the order they happened, before the new assistant reply is appended.
    await identity_service.create_message_for_subject(
        external_subject=subject,
        thread_public_id=thread_id,
        role=MessageRole.USER,
        content=payload.question,
    )

    boundary_state = _classify_question(payload.question)
    if boundary_state.get("intent") == "non_data":
        answer = str(boundary_state.get("answer") or _FALLBACK_ANSWER)
        await identity_service.create_message_for_subject(
            external_subject=subject,
            thread_public_id=thread_id,
            role=MessageRole.ASSISTANT,
            content=answer,
        )
        return _build_stream_response(
            answer=answer,
            query_result={},
            generated_sql=None,
            error_code=None,
        )

    schema_description = shop_schema_loader.load_schema_description()
    whitelist = data_catalog_service.load_sql_whitelist()
    nodes = PromptBackedWorkflowNodes(
        prompt_service=prompt_template_service,
        llm_adapter=chat_llm_adapter,
    )

    answer, query_result, generated_sql, error_code = await _execute_nl2sql_workflow(
        question=payload.question,
        history=history,
        schema_description=schema_description,
        nodes=nodes,
        whitelist=whitelist,
        query_adapter=query_adapter,
    )

    await identity_service.create_message_for_subject(
        external_subject=subject,
        thread_public_id=thread_id,
        role=MessageRole.ASSISTANT,
        content=answer,
    )

    return _build_stream_response(
        answer=answer,
        query_result=query_result,
        generated_sql=generated_sql,
        error_code=error_code,
    )


def _build_stream_response(
    *,
    answer: str,
    query_result: dict[str, Any],
    generated_sql: str | None,
    error_code: str | None,
) -> StreamingResponse:
    run_id = uuid.uuid4().hex
    columns = list(query_result.get("columns") or [])
    sample_rows = [list(row) for row in (query_result.get("rows") or [])[:5]]
    completed_extra: dict[str, object] = {
        "row_count": query_result.get("row_count", 0),
        "truncated": bool(query_result.get("truncated", False)),
        "columns": columns,
        "sample_rows": sample_rows,
    }
    if generated_sql:
        completed_extra["sql"] = generated_sql
    if error_code:
        completed_extra["error_code"] = error_code

    return StreamingResponse(
        iter_llm_sse(
            _build_workflow_chunks(
                generated_sql=generated_sql,
                answer=answer,
                error_code=error_code,
            ),
            run_id=run_id,
            completed_extra=completed_extra,
        ),
        media_type="text/event-stream",
    )


def _classify_question(question: str) -> DataQueryState:
    state: DataQueryState = {"question": question}
    state = input_validation_node(state)
    state = intent_classify_node(state)
    if state.get("intent") == "non_data":
        state = polite_refusal_node(state)
    return state


async def _execute_nl2sql_workflow(
    *,
    question: str,
    history: Sequence[ThreadMessage],
    schema_description: str,
    nodes: PromptBackedWorkflowNodes,
    whitelist: SqlWhitelistSource,
    query_adapter: Any,
) -> tuple[str, dict[str, Any], str | None, str | None]:
    """Run NL2SQL → validate → execute → interpret, with graceful degradation.

    Returns ``(answer, query_result_payload, generated_sql, error_code)``. On
    any stage failure the function returns a short Chinese apology and a stable
    error code so the SSE layer can keep the stream open and persist the
    assistant message to maintain conversation continuity.
    """
    limits = whitelist.policy.limits
    state: DataQueryState = {
        "question": with_conversation_history(question, history),
        "schema_context": schema_description,
    }

    try:
        state = await nodes.sql_generate_node(state)
    except AppError as exc:
        return _app_error_answer(exc), {}, None, exc.code
    except Exception:
        return _nl2sql_failed_answer(), {}, None, "NL2SQL_FAILED"

    sql = str(state.get("generated_sql") or "")
    validation = SqlAstPolicyValidator(whitelist=whitelist).validate(sql)
    if not validation.is_allowed or validation.normalized_sql is None:
        code = (
            validation.first_violation.code.value
            if validation.first_violation is not None
            else "SQL_POLICY_VIOLATION"
        )
        return _sql_policy_answer(), {}, sql or None, code

    try:
        result = await query_adapter.execute(
            QueryExecutionRequest(
                sql=validation.normalized_sql,
                timeout_seconds=limits.timeout_seconds,
                max_rows=limits.max_rows,
                max_fields=limits.max_fields,
                max_bytes=limits.max_bytes,
            )
        )
    except QueryExecutionError as exc:
        return _query_failed_answer(), {}, validation.normalized_sql, exc.code.value

    query_result_payload: dict[str, Any] = {
        "columns": list(result.columns),
        "rows": [list(row) for row in result.rows],
        "row_count": result.row_count,
        "field_count": result.field_count,
        "truncated": result.truncated,
    }
    state["query_result"] = query_result_payload

    try:
        state = await nodes.interpret_node(state)
        answer = str(state.get("answer") or "")
        if not answer:
            answer = _fallback_answer(query_result_payload)
    except Exception:
        answer = _fallback_answer(query_result_payload)

    return answer, query_result_payload, validation.normalized_sql, None


async def _build_workflow_chunks(
    *,
    generated_sql: str | None,
    answer: str,
    error_code: str | None,
) -> AsyncIterator[LlmStreamChunk]:
    """Yield user-safe progress chunks, then answer chunks for the reply."""
    if generated_sql:
        yield LlmStreamChunk(
            kind="thinking",
            text="已识别指标口径并生成安全查询计划。\n",
        )
    if error_code:
        yield LlmStreamChunk(kind="thinking", text=f"执行状态：{error_code}\n")
    for piece in _chunk_text(answer):
        yield LlmStreamChunk(kind="answer", text=piece)


def _fallback_answer(query_result: dict[str, Any]) -> str:
    return ResultInterpretationService().interpret(question="", query_result=query_result)


def _app_error_answer(exc: AppError) -> str:
    if exc.code == "CONFIG_NOT_FOUND":
        return (
            "我还没有拿到可用的真实模型 API Key，所以没有执行 NL2SQL，也没有查询数据库。"
            "请先在 API 配置里启用 DeepSeek 并保存 Key，再发起数据问题。"
        )
    if exc.code in {"CONFIG_KEY_TOO_SHORT", "CONFIG_DECRYPT_FAILED"}:
        return (
            "当前模型配置不可用，所以没有执行 NL2SQL，也没有查询数据库。"
            "请检查 API 配置中的 Key 和加密配置后再试。"
        )
    return f"{_FALLBACK_ANSWER}错误码：{exc.code}。"


def _nl2sql_failed_answer() -> str:
    return "模型调用或 SQL 生成失败，未执行数据库查询。请检查模型配置或稍后重试。"


def _sql_policy_answer() -> str:
    return "生成的查询没有通过 SQL 安全校验，已停止执行数据库查询。请换一种业务问法后再试。"


def _query_failed_answer() -> str:
    return "数据库查询执行失败，未生成可靠结论。请检查只读数据库连接或稍后重试。"


def _chunk_text(text: str, *, chunk_size: int = 24) -> list[str]:
    """Split a string into small deltas for typewriter-style streaming display."""
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


@router.get("/runs/{run_id}", response_model=RunDetailEnvelope)
async def get_run(
    run_id: str,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> RunDetailEnvelope:
    """Return run status projection without exposing generated SQL."""
    run = await _get_owned_run(
        run_id=run_id,
        subject=subject,
        identity_service=identity_service,
        run_trace_service=run_trace_service,
    )
    return RunDetailEnvelope(data=RunDetailResponse.from_entity(run))


@router.get("/runs/{run_id}/stream")
async def stream_run_events(
    run_id: str,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> StreamingResponse:
    """Stream run/node status events as an SSE contract projection."""
    run = await _get_owned_run(
        run_id=run_id,
        subject=subject,
        identity_service=identity_service,
        run_trace_service=run_trace_service,
    )
    node_runs = await run_trace_service.list_node_runs(run=run)
    return StreamingResponse(
        _iter_run_events(run=run, node_runs=tuple(node_runs)),
        media_type="text/event-stream",
    )


@router.post("/runs/{run_id}/cancel", response_model=RunDetailEnvelope)
async def cancel_run(
    run_id: str,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> RunDetailEnvelope:
    """Mark an owned run as canceled without interrupting a real queue."""
    run = await _get_owned_run(
        run_id=run_id,
        subject=subject,
        identity_service=identity_service,
        run_trace_service=run_trace_service,
    )
    if run.id is None:
        raise NotFoundError("run not found")
    canceled = await run_trace_service.cancel_run(run_id=run.id)
    return RunDetailEnvelope(data=RunDetailResponse.from_entity(canceled))


@router.post("/runs/{run_id}/retry", response_model=RunDetailEnvelope)
async def retry_run(
    run_id: str,
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> RunDetailEnvelope:
    """Reset an owned run for retry without scheduling workflow execution."""
    run = await _get_owned_run(
        run_id=run_id,
        subject=subject,
        identity_service=identity_service,
        run_trace_service=run_trace_service,
    )
    if run.id is None:
        raise NotFoundError("run not found")
    retried = await run_trace_service.retry_run(run_id=run.id)
    return RunDetailEnvelope(data=RunDetailResponse.from_entity(retried))


async def _get_owned_run(
    *,
    run_id: str,
    subject: str,
    identity_service: IdentityThreadServiceDep,
    run_trace_service: QueryRunTraceServiceDep,
) -> QueryRun:
    user = await identity_service.get_user_for_subject(external_subject=subject)
    if user is None or user.id is None:
        raise NotFoundError("run not found")
    run = await run_trace_service.get_run_for_user(run_public_id=run_id, user_id=user.id)
    if run is None:
        raise NotFoundError("run not found")
    return run


async def _iter_run_events(*, run: QueryRun, node_runs: tuple[NodeRun, ...]) -> AsyncIterator[str]:
    if run.started_at is not None or run.status in {
        RunStatus.RUNNING,
        RunStatus.SUCCESS,
        RunStatus.FAILED,
    }:
        yield _sse_event("run.started", {"run_id": run.public_id, "status": run.status.value})
    for node_run in node_runs:
        if node_run.started_at is not None or node_run.status in {
            NodeStatus.RUNNING,
            NodeStatus.SUCCESS,
            NodeStatus.FAILED,
            NodeStatus.SKIPPED,
        }:
            yield _sse_event(
                "node.started",
                {
                    "run_id": run.public_id,
                    "node_name": node_run.node_name,
                    "attempt": node_run.attempt,
                },
            )
        if node_run.status in {NodeStatus.SUCCESS, NodeStatus.SKIPPED}:
            yield _sse_event(
                "node.completed",
                {
                    "run_id": run.public_id,
                    "node_name": node_run.node_name,
                    "status": node_run.status.value,
                    "attempt": node_run.attempt,
                },
            )
        if node_run.status is NodeStatus.FAILED:
            yield _sse_event(
                "node.failed",
                {
                    "run_id": run.public_id,
                    "node_name": node_run.node_name,
                    "error_code": node_run.error_code,
                    "attempt": node_run.attempt,
                },
            )
    if run.status is RunStatus.SUCCESS:
        yield _sse_event("run.completed", {"run_id": run.public_id, "status": run.status.value})
    if run.status is RunStatus.FAILED:
        yield _sse_event(
            "run.failed",
            {
                "run_id": run.public_id,
                "status": run.status.value,
                "error_code": run.error_code,
            },
        )


def _sse_event(event_name: str, payload: dict[str, object]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
