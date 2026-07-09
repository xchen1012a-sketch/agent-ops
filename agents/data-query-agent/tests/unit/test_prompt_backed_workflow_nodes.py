"""Unit tests for prompt-backed data-query workflow nodes."""

from __future__ import annotations

import json

import pytest

from data_query_agent.application.services.prompt_template_service import PromptTemplateService
from data_query_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter
from data_query_agent.workflows.prompt_nodes import PromptBackedWorkflowNodes
from data_query_agent.workflows.state import DataQueryState


@pytest.mark.asyncio
async def test_prompt_backed_sql_generate_uses_fake_llm_and_validated_output() -> None:
    adapter = FakeLlmAdapter()
    nodes = PromptBackedWorkflowNodes(
        prompt_service=PromptTemplateService(),
        llm_adapter=adapter,
    )
    state: DataQueryState = {
        "question": "What is the refund amount?",
        "schema_context": "wide_orders",
    }

    result = await nodes.sql_generate_node(state)

    assert result["generated_sql"] == (
        "SELECT SUM(refund_amount) AS refund_amount "
        "FROM wide_orders WHERE is_refunded = 1 LIMIT 100"
    )
    assert result["llm_output"]["confidence"] == 0.8
    assert adapter.requests[0].prompt_name == "nl2sql"
    assert result["node_trace"][-1] == {"node_name": "sql_generate", "status": "completed"}


@pytest.mark.asyncio
async def test_prompt_backed_nodes_prepend_system_policy() -> None:
    adapter = FakeLlmAdapter()
    nodes = PromptBackedWorkflowNodes(
        prompt_service=PromptTemplateService(),
        llm_adapter=adapter,
    )

    await nodes.sql_generate_node({"question": "total sales", "schema_context": "wide_orders"})

    sent = adapter.requests[0].rendered_prompt
    # Identity + refusal policy reaches the model ahead of the task prompt.
    assert "你是「智能问数助手」" in sent
    assert "【拒绝规则】" in sent
    assert "total sales" in sent


@pytest.mark.asyncio
async def test_prompt_backed_sql_generate_rejects_invalid_structured_output() -> None:
    adapter = FakeLlmAdapter(fixtures={("nl2sql", "v1"): json.dumps({"sql": "SELECT 1"})})
    nodes = PromptBackedWorkflowNodes(
        prompt_service=PromptTemplateService(),
        llm_adapter=adapter,
    )

    with pytest.raises(ValueError, match="missing required field"):
        await nodes.sql_generate_node({"question": "total sales", "schema_context": "wide_orders"})


@pytest.mark.asyncio
async def test_prompt_backed_interpret_uses_validated_answer_and_followups() -> None:
    adapter = FakeLlmAdapter(
        fixtures={
            ("interpret_result", "v1"): json.dumps(
                {"answer": "Total sales are 98,765.43.", "followups": ["Show trend"]}
            )
        }
    )
    nodes = PromptBackedWorkflowNodes(
        prompt_service=PromptTemplateService(),
        llm_adapter=adapter,
    )

    result = await nodes.interpret_node(
        {
            "question": "What are total sales?",
            "query_result": {"columns": ["total_sales"], "rows": [[98765.43]]},
        }
    )

    assert result["answer"] == "Total sales are 98,765.43."
    assert result["followups"] == ["Show trend"]
    assert adapter.requests[0].prompt_name == "interpret_result"
    assert result["node_trace"][-1] == {"node_name": "interpret", "status": "completed"}


@pytest.mark.asyncio
async def test_prompt_backed_interpret_rejects_non_json_output() -> None:
    adapter = FakeLlmAdapter(fixtures={("interpret_result", "v1"): "not json"})
    nodes = PromptBackedWorkflowNodes(
        prompt_service=PromptTemplateService(),
        llm_adapter=adapter,
    )

    with pytest.raises(ValueError, match="valid JSON"):
        await nodes.interpret_node({"question": "What are total sales?", "query_result": {}})
