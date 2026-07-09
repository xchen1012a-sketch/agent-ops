"""Fake LLM adapter for prompt-backed workflow tests."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from data_query_agent.domain.ports.llm_adapter import (
    LlmAdapter,
    LlmCompletionRequest,
    LlmCompletionResponse,
    LlmStreamChunk,
)

_STREAM_CHUNK_SIZE = 8


class FakeLlmAdapter(LlmAdapter):
    """Deterministic in-memory LLM adapter that never calls external models."""

    def __init__(self, fixtures: dict[tuple[str, str], str] | None = None) -> None:
        self._fixtures = fixtures or {}
        self.requests: list[LlmCompletionRequest] = []

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        """Return a fixture or a deterministic response for known prompt names."""
        self.requests.append(request)
        fixture = self._fixtures.get((request.prompt_name, request.version))
        if fixture is not None:
            return LlmCompletionResponse(content=fixture)
        return LlmCompletionResponse(content=_default_content(request))

    async def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        """Yield deterministic thinking then answer chunks for local streaming demos."""
        self.requests.append(request)
        for piece in _chunk_text(_default_thinking(request)):
            yield LlmStreamChunk(kind="thinking", text=piece)
        for piece in _chunk_text(_default_answer(request)):
            yield LlmStreamChunk(kind="answer", text=piece)


def _default_thinking(request: LlmCompletionRequest) -> str:
    return (
        f"先理解问题：{request.rendered_prompt.strip()}。"
        "拆解为查询目标与约束，规划最小查询路径，再组织回答。"
    )


def _default_answer(request: LlmCompletionRequest) -> str:
    return (
        "### 回答\n\n"
        f"针对「{request.rendered_prompt.strip()}」，这是一段用于本地演示的确定性回答，"
        "用于验证思考展示与正文流式渲染链路。\n\n"
        "- 思考阶段独立成一条通道\n"
        "- 正文按 markdown 流式呈现\n"
    )


def _chunk_text(text: str, *, chunk_size: int = _STREAM_CHUNK_SIZE) -> list[str]:
    """Split text into small deltas for a typewriter-style streaming display."""
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def _default_content(request: LlmCompletionRequest) -> str:
    if request.prompt_name == "nl2sql":
        return json.dumps(
            {
                "sql": _nl2sql_for_question(request.rendered_prompt),
                "confidence": 0.8,
                "reasoning_summary": "deterministic fake llm mapping",
            }
        )
    if request.prompt_name == "interpret_result":
        return json.dumps(
            {
                "answer": _interpret_from_prompt(request.rendered_prompt),
                "followups": [],
            }
        )
    raise ValueError(f"fake LLM fixture not registered: {request.prompt_name}@{request.version}")


def _nl2sql_for_question(prompt: str) -> str:
    """Map a Chinese business question to a real-schema SELECT against shop_db.

    The fake LLM cannot actually reason about language, but the demo questions
    in the coursework fall into a small set of shapes (total / refund / by-region
    / by-channel / by-category / by-brand / monthly trend / by customer level).
    We keyword-route to a hand-written SELECT that uses the real wide_orders or
    wide_order_details columns so the SQL whitelist accepts it and shop_db
    returns real rows.
    """
    text = prompt.lower()

    has_refund = "refund" in text or "退款" in text
    has_region = "region" in text or "地区" in text or "区域" in text or "地区" in text
    has_channel = "channel" in text or "渠道" in text
    has_category = "categ" in text or "品类" in text or "类别" in text or "分类" in text
    has_brand = "brand" in text or "品牌" in text
    has_month = "month" in text or "月" in text
    has_customer_level = "customer_level" in text or "客户等级" in text or "会员" in text
    has_product = "product" in text or "商品" in text or "产品" in text

    amount_col = "refund_amount" if has_refund else "actual_amount"
    label = "refund_amount" if has_refund else "total_sales"

    if has_region:
        return (
            f"SELECT region_name, SUM({amount_col}) AS {label} "
            "FROM wide_orders GROUP BY region_name "
            f"ORDER BY SUM({amount_col}) DESC LIMIT 100"
        )
    if has_channel:
        return (
            f"SELECT channel_name, SUM({amount_col}) AS {label} "
            "FROM wide_orders GROUP BY channel_name "
            f"ORDER BY SUM({amount_col}) DESC LIMIT 100"
        )
    if has_customer_level:
        return (
            f"SELECT customer_level, SUM({amount_col}) AS {label} "
            "FROM wide_orders GROUP BY customer_level "
            f"ORDER BY SUM({amount_col}) DESC LIMIT 100"
        )
    if has_category:
        return (
            f"SELECT category_name, SUM({amount_col}) AS {label} "
            "FROM wide_order_details GROUP BY category_name "
            f"ORDER BY SUM({amount_col}) DESC LIMIT 100"
        )
    if has_brand:
        return (
            f"SELECT brand, SUM({amount_col}) AS {label} "
            "FROM wide_order_details GROUP BY brand "
            f"ORDER BY SUM({amount_col}) DESC LIMIT 100"
        )
    if has_product:
        return (
            f"SELECT product_name, SUM({amount_col}) AS {label} "
            "FROM wide_order_details GROUP BY product_name "
            f"ORDER BY SUM({amount_col}) DESC LIMIT 100"
        )
    if has_month:
        return (
            f"SELECT order_month, SUM({amount_col}) AS {label} "
            "FROM wide_orders GROUP BY order_month "
            f"ORDER BY order_month LIMIT 100"
        )
    if has_refund:
        return (
            f"SELECT SUM(refund_amount) AS refund_amount "
            "FROM wide_orders WHERE refund_amount > 0 LIMIT 100"
        )
    return f"SELECT SUM({amount_col}) AS {label} FROM wide_orders LIMIT 100"


def _interpret_from_prompt(rendered_prompt: str) -> str:
    """Best-effort: pull the first row from the result_summary JSON in the
    rendered prompt so the demo answer carries a real number even without a
    real DeepSeek key. When the result has many rows (a ranking), list the
    top 3.
    """
    payload = _extract_first_json_object(rendered_prompt)
    if not isinstance(payload, dict):
        return "结论：查询结果已生成。"
    columns = payload.get("columns")
    rows = payload.get("rows")
    if not isinstance(columns, list) or not isinstance(rows, list) or not rows:
        return "结论：查询结果已生成。"

    if len(rows) == 1 and len(columns) <= 2:
        label = str(columns[-1])
        value = rows[0][-1] if isinstance(rows[0], list) and rows[0] else None
        if value is None:
            return "结论：查询未返回有效数据。"
        return f"结论：{label} 为 {_format_value(value)}。"

    parts = [f"结论：共返回 {len(rows)} 行，前 {min(3, len(rows))} 名如下。"]
    for row in rows[:3]:
        if not isinstance(row, list) or not row:
            continue
        dimension = row[0]
        metric = row[-1]
        parts.append(f"- {_format_value(dimension)}：{_format_value(metric)}")
    return "\n".join(parts)


def _extract_first_json_object(text: str) -> object | None:
    start = text.find("{")
    while start != -1:
        candidate = _scan_json_object(text, start)
        if candidate is not None:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
        start = text.find("{", start + 1)
    return None


def _scan_json_object(text: str, start: int) -> str | None:
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _format_value(value: object) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not value.is_integer():
            return f"{value:,.2f}"
        return f"{value:,}"
    return str(value)
