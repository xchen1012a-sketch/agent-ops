"""Boundary behavior tests for the data-query assistant entry point."""

from __future__ import annotations

import pytest

from data_query_agent.api.v1.endpoints.runs import _execute_nl2sql_workflow
from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.core.errors import ConfigNotFoundError
from data_query_agent.workflows.nodes import (
    input_validation_node,
    intent_classify_node,
    polite_refusal_node,
)
from data_query_agent.workflows.state import DataQueryState


def _classify(question: str) -> DataQueryState:
    state: DataQueryState = {"question": question}
    state = input_validation_node(state)
    state = intent_classify_node(state)
    if state.get("intent") == "non_data":
        state = polite_refusal_node(state)
    return state


def test_greeting_returns_agent_intro_without_sql_path() -> None:
    state = _classify("你好")

    assert state["intent"] == "non_data"
    assert state["response_tier"] == "greeting"
    assert "智能问数助手" in state["answer"]
    assert "generated_sql" not in state


def test_ambiguous_request_asks_for_metric_and_time_range() -> None:
    state = _classify("帮我看看")

    assert state["intent"] == "non_data"
    assert state["response_tier"] == "clarify"
    assert "指标" in state["answer"]
    assert "时间范围" in state["answer"]
    assert "generated_sql" not in state


class _ConfigMissingNodes:
    async def sql_generate_node(self, state: DataQueryState) -> DataQueryState:
        raise ConfigNotFoundError("missing model config")


@pytest.mark.asyncio
async def test_missing_model_config_does_not_fall_back_to_mock_sql() -> None:
    answer, query_result, generated_sql, error_code = await _execute_nl2sql_workflow(
        question="本月销售额是多少",
        history=tuple(),
        schema_description="CREATE TABLE wide_orders(actual_amount decimal(12,2));",
        nodes=_ConfigMissingNodes(),  # type: ignore[arg-type]
        whitelist=DataCatalogService().load_sql_whitelist(),
        query_adapter=object(),
    )

    assert error_code == "CONFIG_NOT_FOUND"
    assert generated_sql is None
    assert query_result == {}
    assert "没有执行 NL2SQL" in answer
    assert "没有查询数据库" in answer
