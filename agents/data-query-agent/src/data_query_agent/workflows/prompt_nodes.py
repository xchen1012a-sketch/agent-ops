"""Prompt-backed workflow nodes with injectable LLM adapter."""

from __future__ import annotations

import json
from typing import Literal

from data_query_agent.application.services.prompt_template_service import PromptTemplateService
from data_query_agent.application.services.result_interpretation_service import (
    ResultInterpretationService,
)
from data_query_agent.application.services.result_projection_service import ResultProjectionService
from data_query_agent.domain.ports.llm_adapter import LlmAdapter, LlmCompletionRequest
from data_query_agent.prompts.policy import with_system_policy
from data_query_agent.workflows.state import DataQueryState, NodeTrace


class PromptBackedWorkflowNodes:
    """LLM-backed node boundary that validates structured outputs before state use."""

    def __init__(
        self,
        *,
        prompt_service: PromptTemplateService,
        llm_adapter: LlmAdapter,
        version: str = "v1",
    ) -> None:
        self._prompt_service = prompt_service
        self._llm_adapter = llm_adapter
        self._version = version

    async def sql_generate_node(self, state: DataQueryState) -> DataQueryState:
        """Generate a SQL candidate from validated prompt output."""
        template = self._prompt_service.load_template(prompt_name="nl2sql", version=self._version)
        rendered = self._prompt_service.render(
            template=template,
            variables={
                "question": state.get("question", ""),
                "schema_summary": state.get("schema_context", ""),
            },
        )
        response = await self._llm_adapter.complete(
            LlmCompletionRequest(
                prompt_name=template.name,
                version=template.version,
                rendered_prompt=with_system_policy(rendered),
            )
        )
        output = self._prompt_service.validate_output(
            template=template, raw_output=response.content
        )
        sql = output["sql"]
        if not isinstance(sql, str):
            raise ValueError("validated SQL output must be a string")
        next_state: DataQueryState = {
            **state,
            "generated_sql": sql,
            "llm_output": output,
        }
        return _with_trace(next_state, "sql_generate", "completed")

    async def interpret_node(self, state: DataQueryState) -> DataQueryState:
        """Interpret query results from validated prompt output."""
        template = self._prompt_service.load_template(
            prompt_name="interpret_result",
            version=self._version,
        )
        rendered = self._prompt_service.render(
            template=template,
            variables={
                "question": state.get("question", ""),
                "result_summary": _result_summary(state.get("query_result", {})),
            },
        )
        response = await self._llm_adapter.complete(
            LlmCompletionRequest(
                prompt_name=template.name,
                version=template.version,
                rendered_prompt=with_system_policy(rendered),
            )
        )
        output = self._prompt_service.validate_output(
            template=template, raw_output=response.content
        )
        answer = output["answer"]
        if not isinstance(answer, str):
            raise ValueError("validated answer output must be a string")
        followups = _followups(output)
        if not followups and isinstance(state.get("query_result"), dict):
            followups = ResultProjectionService().project(
                question=state.get("question", ""),
                query_result=state["query_result"],
            ).followups
        if _needs_deterministic_interpretation(answer) and isinstance(
            state.get("query_result"), dict
        ):
            answer = ResultInterpretationService().interpret(
                question=state.get("question", ""),
                query_result=state["query_result"],
                followups=followups,
            )
        next_state: DataQueryState = {**state, "answer": answer, "llm_output": output}
        if "chart" in output:
            next_state["chart"] = output["chart"]
        if followups:
            next_state["followups"] = list(followups)
        return _with_trace(next_state, "interpret", "completed")


def _result_summary(query_result: object) -> str:
    if not isinstance(query_result, dict):
        return "no structured result"
    return json.dumps(query_result, ensure_ascii=False, default=str)


def _followups(output: dict[str, object]) -> tuple[str, ...]:
    value = output.get("followups")
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def _needs_deterministic_interpretation(answer: str) -> bool:
    normalized = answer.strip()
    return normalized in {
        "",
        "结论：查询结果已生成。",
        "查询结果已生成。",
        "已生成查询结果。",
    }


def _with_trace(
    state: DataQueryState,
    node_name: str,
    status: Literal["started", "completed", "failed", "skipped"],
) -> DataQueryState:
    trace = list(state.get("node_trace", []))
    trace.append(NodeTrace(node_name=node_name, status=status))
    return {**state, "node_trace": trace}
