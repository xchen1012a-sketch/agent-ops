"""Pure LEGAL-140 workflow nodes with external services behind mock boundaries."""

from __future__ import annotations

import re

from legal_consulting_agent.workflows.legal_state import (
    Citation,
    LegalEntityHints,
    LegalWorkflowState,
    LegalWorkflowUpdate,
    RetrievalChunk,
)

NON_LEGAL_MESSAGE = (
    "我是法律咨询助手，可以就劳动用工、合同纠纷、婚姻家庭、公司经营、"
    "刑事风险、债务赔偿等常见法律问题提供参考意见。你的问题看起来与法律无关，"
    "如果确有法律方面的困扰，请描述你遇到的具体情况，我会尽力帮你分析。"
)
NO_SOURCE_DISCLAIMER = "本回答未在知识库中找到对应依据，仅供参考。"

# Professional-assistant boundary messages. Every tier restates the identity.
#   * anchor_light (first off-topic turn): brief, no substantive answer.
#   * redirect_firm (repeated off-topic): decline and steer back.
#   * adversarial: hard refuse role-swap / instruction or secret disclosure.
ANCHOR_LIGHT_MESSAGE = (
    "这个问题稍微超出了我的范围，我就不展开了。我是法律咨询助手，"
    "遇到劳动、合同、婚姻家庭、公司、刑事或债务方面的问题，我能帮你分析。"
)
REDIRECT_FIRM_MESSAGE = (
    "我还是专注在法律咨询上，这个问题就不展开了。如果你有劳动、合同、"
    "婚姻家庭、公司、刑事或债务方面的困扰，告诉我具体情况，我来帮你。"
)
ADVERSARIAL_REFUSAL_MESSAGE = (
    "我不能切换身份、泄露内部指令或密钥，也不能提供他人的隐私信息。"
    "我是法律咨询助手，有法律方面的问题我很乐意帮你。"
)


def _off_topic_message(offtopic_streak: int) -> str:
    """Escalate from a gentle anchor to a firm redirect as off-topic persists."""
    return REDIRECT_FIRM_MESSAGE if offtopic_streak >= 2 else ANCHOR_LIGHT_MESSAGE

# Scope recognition for the legal agent.
#
# Design principle — fail-open on scope, fail-closed on safety:
#   * A matched category answers with that category's framing.
#   * A question that matches no category but shows no off-topic signal is
#     treated as a GENERAL legal question and answered best-effort with a
#     disclaimer — NOT refused. A real legal question ("房东不退押金怎么办")
#     must never be turned away just because it misses a keyword.
#   * Only an explicit off-topic signal (weather, poem, coding...) is declined,
#     and even then with a helpful boundary message.
# Safety gating (prompt injection, personal-safety risk) is handled separately
# and remains fail-closed.
_CATEGORY_KEYWORDS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "family",
        "询问婚姻家庭争议",
        ("离婚", "抚养", "婚姻", "彩礼", "财产分割", "继承", "遗产", "赡养", "家暴", "夫妻"),
    ),
    (
        "criminal",
        "询问刑事法律风险",
        ("犯罪", "刑事", "拘留", "逮捕", "取保", "判刑", "量刑", "盗窃", "诈骗", "故意伤害"),
    ),
    (
        "civil_labor",
        "询问劳动合同或用工争议",
        (
            "劳动", "合同", "公司", "调岗", "辞退", "加班", "工资", "社保",
            "试用期", "裁员", "离职", "工伤", "拖欠", "竞业",
        ),
    ),
    (
        "contract",
        "询问争议解决路径",
        (
            "起诉", "官司", "赔偿", "违约", "债务", "欠款", "押金", "定金",
            "退款", "维权", "消费", "房东", "租房", "物业",
        ),
    ),
)
_OFF_TOPIC_KEYWORDS = (
    "写诗", "作诗", "笑话", "讲个故事", "天气", "翻译", "菜谱", "食谱",
    "写代码", "编程", "数学题", "股票", "彩票", "唱歌", "作文",
)
PROMPT_INJECTION_PATTERNS = (
    # instruction override
    "ignore previous instructions", "ignore previous", "ignore above",
    "disregard previous", "output secrets", "system prompt",
    "reveal your instructions", "developer mode", "dan mode", "jailbreak",
    # identity swap
    "you are now", "from now on you are", "pretend you are", "pretend to be",
    # secret / data exfiltration
    "output your api key", "print your api key",
    # Chinese
    "泄露密钥", "输出密钥", "打印密钥", "忽略以上", "忽略之前", "无视以上",
    "系统提示词", "系统提示", "你的提示词", "内部指令",
    "你现在是", "从现在起你是", "从现在开始你是", "假装你是", "扮演成",
    "开发者模式", "越狱模式", "导出所有用户", "其他用户的",
)
HIGH_RISK_KEYWORDS = ("自杀", "轻生", "人身安全", "家暴", "紧急")
STATUTE_PATTERN = re.compile(r"第[一二三四五六七八九十百零\d]+条")


def _trace(state: LegalWorkflowState, node_name: str) -> list[str]:
    return [*state.get("node_trace", []), node_name]


def input_safety_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Normalize user input and block prompt-injection style instructions."""

    question = state["question"].strip()
    lowered = question.lower()
    blocked = not question or any(pattern in lowered for pattern in PROMPT_INJECTION_PATTERNS)
    if blocked:
        return {
            "safe_question": None,
            "is_safe": False,
            "response_tier": "refuse_adversarial",
            "error_code": "INPUT_BLOCKED",
            "boundary_message": ADVERSARIAL_REFUSAL_MESSAGE,
            "node_trace": _trace(state, "input_safety"),
        }
    return {
        "safe_question": question,
        "is_safe": True,
        "error_code": None,
        "node_trace": _trace(state, "input_safety"),
    }


def classification_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Classify a safe legal question without calling an LLM in the first slice."""

    if not state.get("is_safe", False):
        return {"node_trace": _trace(state, "classification")}

    question = state.get("safe_question") or ""

    category = None
    intent = ""
    for candidate_category, candidate_intent, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in question for keyword in keywords):
            category = candidate_category
            intent = candidate_intent
            break

    prior_streak = state.get("offtopic_streak", 0)
    if category is None:
        if any(keyword in question for keyword in _OFF_TOPIC_KEYWORDS):
            category = "other"
            intent = "识别为非法律问题"
        else:
            # Fail-open: an unmatched question is answered as a general legal
            # question with a disclaimer rather than refused as "other".
            category = "general"
            intent = "未命中细分类目，按一般法律问题处理"

    # Off-topic escalates the streak (gentle anchor -> firm redirect); any
    # answerable legal question resets it.
    if category == "other":
        offtopic_streak = prior_streak + 1
        response_tier = "redirect_firm" if offtopic_streak >= 2 else "anchor_light"
    else:
        offtopic_streak = 0
        response_tier = "in_scope"

    entities: LegalEntityHints = {
        "statute_numbers": STATUTE_PATTERN.findall(question),
        "statute_names": [name for name in ("劳动合同法", "民法典") if name in question],
        "case_keywords": [word for word in ("调岗", "离婚", "赔偿", "合同") if word in question],
    }
    return {
        "category": category,
        "intent": intent,
        "legal_entities": entities,
        "response_tier": response_tier,
        "offtopic_streak": offtopic_streak,
        "node_trace": _trace(state, "classification"),
    }


# Claude-style memory: keep a generous window of prior turns so the model has
# real multi-turn context, not just the last exchange. Bounded to cap tokens.
CONTEXT_WINDOW_MESSAGES = 20


def context_build_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Trim the conversation history to the memory window before generation."""

    existing_context = state.get("context_messages", [])
    return {
        "context_messages": existing_context[-CONTEXT_WINDOW_MESSAGES:],
        "node_trace": _trace(state, "context_build"),
    }


def retrieval_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Return adapter-provided chunks or an explicit no-source path.

    Real BGE/Qdrant retrieval is intentionally not called in this slice. Later
    slices can replace ``mock_chunks`` with an adapter result while preserving
    this node contract.
    """

    if state.get("error_code"):
        return {"node_trace": _trace(state, "retrieval")}
    chunks = state.get("mock_chunks", [])
    return {
        "chunks": chunks,
        "node_trace": _trace(state, "retrieval"),
    }


def _citation_from_chunk(chunk: RetrievalChunk) -> Citation:
    return {
        "source": chunk["source_name"],
        "section": chunk["source_section"],
        "snippet": chunk["snippet"],
    }


def generation_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Generate a deterministic draft without calling DeepSeek."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "generation")}

    question = state.get("safe_question") or ""
    category = state.get("category")
    chunks = state.get("chunks", [])
    if category == "other":
        # Off-topic: brief anchor on the first turn, firm redirect if it
        # persists — never a substantive answer to the unrelated question.
        return {
            "answer_draft": _off_topic_message(state.get("offtopic_streak", 1)),
            "citations": [],
            "node_trace": _trace(state, "generation"),
        }
    if not chunks:
        return {
            "answer_draft": f"针对“{question}”，需要结合事实和适用法律进一步判断。{NO_SOURCE_DISCLAIMER}",
            "citations": [],
            "node_trace": _trace(state, "generation"),
        }

    first_chunk = chunks[0]
    citation = _citation_from_chunk(first_chunk)
    return {
        "answer_draft": (
            f"针对“{question}”，可先参考{citation['source']} {citation['section']}："
            f"{citation['snippet']} 本回答仅供参考，不构成正式法律意见。"
        ),
        "citations": [citation],
        "node_trace": _trace(state, "generation"),
    }


def citation_check_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Ensure generated citations are backed by retrieved chunks."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "citation_check")}

    citations = state.get("citations", [])
    chunks = state.get("chunks", [])
    source_keys = {
        (chunk["source_name"], chunk["source_section"], chunk["snippet"]) for chunk in chunks
    }
    invalid = [
        citation
        for citation in citations
        if (citation["source"], citation["section"], citation["snippet"]) not in source_keys
    ]
    if invalid:
        return {
            "validated_answer": None,
            "error_code": "CITATION_INVALID",
            "node_trace": _trace(state, "citation_check"),
        }
    return {
        "validated_answer": state.get("answer_draft"),
        "node_trace": _trace(state, "citation_check"),
    }


def risk_check_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Mark high-risk questions for later human-review queue integration."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "risk_check")}

    text = f"{state.get('safe_question') or ''} {state.get('validated_answer') or ''}"
    high_risk = any(keyword in text for keyword in HIGH_RISK_KEYWORDS)
    return {
        "high_risk": high_risk,
        "risk_reason": "personal_safety" if high_risk else None,
        "node_trace": _trace(state, "risk_check"),
    }


def persist_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Expose the persistence boundary without writing to the database yet."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "persist")}
    if state.get("simulate_db_unavailable", False):
        return {
            "message_id": None,
            "error_code": "DB_UNAVAILABLE",
            "node_trace": _trace(state, "persist"),
        }
    return {
        "message_id": state.get("message_id"),
        "node_trace": _trace(state, "persist"),
    }
