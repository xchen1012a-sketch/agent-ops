"""Deterministic data-query workflow nodes."""

from __future__ import annotations

from typing import Any, Literal

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.application.services.result_interpretation_service import (
    ResultInterpretationService,
)
from data_query_agent.application.services.result_projection_service import ResultProjectionService
from data_query_agent.domain.policies.sql_ast import SqlAstPolicyValidator
from data_query_agent.domain.value_objects.data_catalog import EvaluationFixture
from data_query_agent.workflows.state import DataQueryState, NodeTrace

# Scope recognition for the data-query agent.
#
# Design principle — fail-open on scope, fail-closed on safety:
#   * A positive data signal -> answer. The vocabulary is deliberately broad
#     and bilingual so an in-scope question is never rejected merely because it
#     used a synonym ("revenue", "营收") or Chinese wording.
#   * No data signal but a clear off-topic signal -> a helpful boundary reply
#     that states what this agent CAN do and invites an in-scope question.
#   * Neither signal (ambiguous) -> we do NOT fabricate SQL and we do NOT slam
#     the door; we ask one short clarifying question.
# These lists are priors, not gates: "unrecognized" means "ask", not "reject".
_DATA_SIGNALS = (
    # English — metrics / entities
    "sales", "revenue", "gmv", "order", "orders", "amount", "refund", "refunds",
    "margin", "profit", "cost", "customer", "customers", "region", "regions",
    "trend", "growth", "metric", "kpi", "conversion", "retention", "churn",
    # Chinese - readable MVP fixture vocabulary
    "销售", "销售额", "营收", "收入", "订单", "退款", "退款率", "毛利",
    "利润", "客户", "客单价", "地区", "区域", "渠道", "品类", "品牌",
    "商品", "支付", "趋势", "排行", "周末", "工作日", "总销售额",
    # English — analytical shape
    "how many", "how much", "total", "count", "average", "sum", "top",
    "compare", "breakdown", "distribution", "ratio", "percentage",
    # Chinese — metrics / entities
    "销售", "销售额", "营收", "营业额", "收入", "订单", "退款", "退货",
    "利润", "毛利", "成本", "客户", "客单价", "地区", "区域", "门店",
    "品类", "商品", "金额", "数量", "指标", "转化", "复购", "留存",
    # Chinese — analytical shape
    "多少", "几个", "统计", "汇总", "合计", "占比", "排名", "趋势",
    "环比", "同比", "平均", "总计", "报表", "对比", "分布",
)

# Positive off-topic signals — only these justify declining, and even then the
# reply stays helpful and points back toward the agent's real capability.
_OFF_TOPIC_SIGNALS = (
    "poem", "story", "joke", "song", "lyrics", "weather", "translate",
    "recipe", "essay",
    "写诗", "作诗", "笑话", "讲个故事", "唱歌", "歌词", "天气", "翻译",
    "菜谱", "食谱", "作文",
)

_GREETING_SIGNALS = (
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "你好", "您好", "嗨", "在吗", "早上好", "下午好", "晚上好",
)

_CAPABILITY_LINE = (
    "我是智能问数助手，可以回答订单、销售额、营收、退款、利润、客户、地区和业务趋势问题。"
)

# Adversarial guard (Layer 1 — deterministic, defense-in-depth).
#
# These are unambiguous jailbreak / role-swap / secret-exfiltration markers.
# The list is deliberately conservative (standard set) to avoid flagging normal
# business questions; nuanced novel attacks are the LLM system prompt's job.
# A match forces the "refuse_adversarial" tier regardless of topic.
_ADVERSARIAL_PATTERNS = (
    # instruction override
    "ignore previous", "ignore above", "ignore all previous", "disregard previous",
    "system prompt", "reveal your instructions", "reveal the system prompt",
    "developer mode", "dan mode", "jailbreak",
    # identity swap
    "you are now", "from now on you are", "pretend you are", "pretend to be",
    # secret / data exfiltration
    "output your api key", "print your api key", "exfiltrate", "leak the",
    # Chinese
    "忽略以上", "忽略之前", "忽略前面", "无视以上", "无视之前",
    "系统提示词", "系统提示", "你的提示词", "内部指令",
    "你现在是", "从现在起你是", "从现在开始你是", "假装你是", "扮演成",
    "开发者模式", "越狱模式", "输出密钥", "泄露密钥", "打印密钥",
    "导出所有用户", "其他用户的", "别人的订单",
)


def _is_adversarial(normalized_question: str) -> bool:
    return any(pattern in normalized_question for pattern in _ADVERSARIAL_PATTERNS)


def input_validation_node(state: DataQueryState) -> DataQueryState:
    """Normalize and validate the incoming question."""
    question = state.get("question", "").strip()
    next_state: DataQueryState = {**state, "question": question}
    return _with_trace(next_state, "input_validation", "completed")


def intent_classify_node(state: DataQueryState) -> DataQueryState:
    """Assign a response tier: answer in-scope, anchor/redirect off-topic, or refuse.

    Tiers (professional-assistant policy):
      * data_query          -> in scope, answer fully.
      * refuse_adversarial  -> jailbreak / role-swap / exfiltration, hard refuse.
      * anchor_light        -> first off-topic turn: brief acknowledgement + a
                               one-line identity anchor (no substantive answer).
      * redirect_firm       -> repeated off-topic: decline and steer back.
    ``offtopic_streak`` carries the count of consecutive off-topic turns so the
    agent escalates from a gentle anchor to a firm redirect ("过度就拉回来").
    """
    normalized = state.get("question", "").lower()
    prior_streak = state.get("offtopic_streak", 0)

    if _is_adversarial(normalized):
        next_state: DataQueryState = {
            **state,
            "intent": "non_data",
            "response_tier": "refuse_adversarial",
            "offtopic_streak": prior_streak,
            "refusal_reason": "adversarial or unsafe instruction",
        }
        return _with_trace(next_state, "intent_classify", "completed")

    if normalized in _GREETING_SIGNALS:
        next_state = {
            **state,
            "intent": "non_data",
            "intent_confidence": "high",
            "response_tier": "greeting",
            "offtopic_streak": 0,
        }
        return _with_trace(next_state, "intent_classify", "completed")

    if any(signal in normalized for signal in _DATA_SIGNALS):
        next_state = {
            **state,
            "intent": "data_query",
            "intent_confidence": "high",
            "response_tier": "in_scope",
            "offtopic_streak": 0,
        }
        return _with_trace(next_state, "intent_classify", "completed")

    if not any(signal in normalized for signal in _OFF_TOPIC_SIGNALS):
        next_state = {
            **state,
            "intent": "non_data",
            "intent_confidence": "low",
            "response_tier": "clarify",
            "offtopic_streak": 0,
            "refusal_reason": "ambiguous data-query request; ask for metric and time range",
        }
        return _with_trace(next_state, "intent_classify", "completed")

    streak = prior_streak + 1
    tier: Literal["anchor_light", "redirect_firm"] = (
        "redirect_firm" if streak >= 2 else "anchor_light"
    )
    next_state = {
        **state,
        "intent": "non_data",
        "intent_confidence": "low",
        "response_tier": tier,
        "offtopic_streak": streak,
        "refusal_reason": "outside data-query scope; anchored to agent role",
    }
    return _with_trace(next_state, "intent_classify", "completed")


def schema_retrieval_node(state: DataQueryState) -> DataQueryState:
    """Attach deterministic schema context from versioned catalog sources."""
    catalog = DataCatalogService().load_schema_catalog()
    table_names = ", ".join(sorted(catalog.table_names()))
    next_state: DataQueryState = {**state, "schema_context": table_names}
    return _with_trace(next_state, "schema_retrieval", "completed")


def sql_generate_node(state: DataQueryState) -> DataQueryState:
    """Generate deterministic SQL without calling an LLM."""
    fixture = _fixture_for_question(state.get("question", ""))
    if fixture is not None:
        return _with_trace(
            {**state, "generated_sql": fixture.baseline_sql, "fixture_case_id": fixture.case_id},
            "sql_generate",
            "completed",
        )

    question = state.get("question", "").lower()
    if "refund" in question:
        sql = (
            "SELECT SUM(refund_amount) AS refund_amount "
            "FROM wide_orders WHERE refund_amount > 0 LIMIT 100"
        )
    else:
        sql = "SELECT SUM(actual_amount) AS total_sales FROM wide_orders LIMIT 100"
    next_state: DataQueryState = {**state, "generated_sql": sql}
    return _with_trace(next_state, "sql_generate", "completed")


def sql_policy_check_node(state: DataQueryState) -> DataQueryState:
    """Validate generated SQL against AST and whitelist policy."""
    whitelist = DataCatalogService().load_sql_whitelist()
    result = SqlAstPolicyValidator(whitelist=whitelist).validate(state.get("generated_sql", ""))
    next_state: DataQueryState = {**state, "policy_allowed": result.is_allowed}
    if not result.is_allowed and result.first_violation is not None:
        next_state["policy_error_code"] = result.first_violation.code.value
    return _with_trace(next_state, "sql_policy_check", "completed")


def query_execute_node(state: DataQueryState) -> DataQueryState:
    """Return a deterministic fake query result without opening a database connection."""
    if not state.get("policy_allowed", False):
        return _with_trace(state, "query_execute", "skipped")
    sql = state.get("generated_sql", "")
    fixture = _fixture_for_sql(sql)
    if fixture is not None:
        query_result_payload: dict[str, Any] = {
            "columns": list(fixture.expected_result.columns),
            "rows": [list(row) for row in fixture.expected_result.rows],
        }
    elif "refund_amount" in sql:
        query_result_payload = {"columns": ["refund_amount"], "rows": [[1234.5]]}
    else:
        query_result_payload = {"columns": ["total_sales"], "rows": [[98765.43]]}
    next_state: DataQueryState = {**state, "query_result": query_result_payload}
    return _with_trace(next_state, "query_execute", "completed")


def result_validate_node(state: DataQueryState) -> DataQueryState:
    """Validate deterministic result presence for the main path."""
    if "query_result" not in state:
        return _with_trace(state, "result_validate", "skipped")
    return _with_trace(state, "result_validate", "completed")


def interpret_node(state: DataQueryState) -> DataQueryState:
    """Produce deterministic interpretation with chart and follow-up semantics."""
    result = state.get("query_result", {})
    projection = (
        ResultProjectionService().project(
            question=state.get("question", ""),
            query_result=result,
        )
        if isinstance(result, dict)
        else None
    )
    followups = tuple(projection.followups) if projection is not None else ()
    answer = (
        ResultInterpretationService().interpret(
            question=state.get("question", ""),
            query_result=result,
            followups=followups,
        )
        if isinstance(result, dict)
        else "结论：当前没有查到可用结果。"
    )
    next_state: DataQueryState = {**state, "answer": answer}
    if projection is not None:
        if projection.chart is not None:
            next_state["chart"] = {
                "type": projection.chart.type,
                "dataset": projection.chart.dataset,
                "encoding": projection.chart.encoding,
            }
        next_state["followups"] = list(followups)
    return _with_trace(next_state, "interpret", "completed")


def persist_audit_node(state: DataQueryState) -> DataQueryState:
    """Mark audit persistence boundary without touching a database."""
    return _with_trace(state, "persist_audit", "completed")


def polite_refusal_node(state: DataQueryState) -> DataQueryState:
    """Render the boundary reply for the assigned tier.

    All tiers restate the agent's identity. Off-topic tiers stay friendly and
    invite an in-scope question; the adversarial tier refuses role changes and
    data exfiltration outright.
    """
    tier = state.get("response_tier", "anchor_light")
    if tier == "refuse_adversarial":
        answer = (
            "我不能更换身份、泄露内部指令或密钥，也不能返回本工作区之外的数据。"
            f"{_CAPABILITY_LINE} 你可以问一个合法的业务数据问题。"
        )
    elif tier == "greeting":
        answer = (
            "你好，我是智能问数助手。你可以直接问销售额、订单、退款、城市/地区排行、趋势对比等业务数据问题。"
            "例如：「本月销售额最高的城市是哪个？」"
        )
    elif tier == "clarify":
        answer = (
            "我可以帮你查业务数据。你想看哪个指标、时间范围和分析维度？"
            "例如可以问：「上个月各地区销售额是多少？」"
        )
    elif tier == "redirect_firm":
        answer = (
            "这个问题超出了我的范围，我会继续专注在业务数据分析上。"
            f"{_CAPABILITY_LINE} 例如可以问：「上个月各地区销售额是多少？」"
        )
    else:  # anchor_light — first off-topic turn
        answer = (
            "这个问题有点偏离问数范围，我先不展开。"
            f"{_CAPABILITY_LINE} 你可以问：「本周退款量是多少？」"
        )
    next_state: DataQueryState = {**state, "answer": answer}
    return _with_trace(next_state, "polite_refusal", "completed")


def route_after_intent(state: DataQueryState) -> str:
    """Route out-of-scope questions to the boundary reply, data questions to the main path."""
    return "polite_refusal" if state.get("intent") == "non_data" else "schema_retrieval"


def _with_trace(
    state: DataQueryState,
    node_name: str,
    status: Literal["started", "completed", "failed", "skipped"],
) -> DataQueryState:
    trace = list(state.get("node_trace", []))
    trace.append(NodeTrace(node_name=node_name, status=status))
    return {**state, "node_trace": trace}


def _fixture_for_question(question: str) -> EvaluationFixture | None:
    normalized_question = question.strip().lower()
    if not normalized_question:
        return None
    fixtures = DataCatalogService().load_evaluation_fixtures().fixtures
    for fixture in fixtures:
        if fixture.question.strip().lower() == normalized_question:
            return fixture
    return None


def _fixture_for_sql(sql: str) -> EvaluationFixture | None:
    normalized_sql = _normalize_sql(sql)
    if not normalized_sql:
        return None
    fixtures = DataCatalogService().load_evaluation_fixtures().fixtures
    for fixture in fixtures:
        if _normalize_sql(fixture.baseline_sql) == normalized_sql:
            return fixture
    return None


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split())
