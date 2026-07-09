"""Parse Feishu messages and build user-facing text."""

from __future__ import annotations

import json
import re
from typing import Any

from app.models.schemas import FeishuIncomingMessage, FeishuMessageBody, FeishuSender
from app.utils.logging import get_logger

user_logger = get_logger("app.feishu.user")

MAX_CARD_BYTES = 30720
TRUNCATE_SUFFIX = "\n\n...(内容过长已截断)"

MSG_UNSUPPORTED = "暂仅支持文本消息。"
MSG_HUMAN_INPUT = "该问题需要人工处理，请稍后再试。"
MSG_DIFY_ERROR = "抱歉，处理失败，请联系管理员。"
MSG_DIFY_TIMEOUT = "处理超时，请简化问题后重试。"
MSG_SERVICE_ERROR = "系统繁忙，请稍后重试。"
MSG_DIFY_UNAVAILABLE = "服务暂时不可用，请稍后重试。"
MSG_DIFY_STRUCTURED_OUTPUT = (
    "工作流执行失败：模型输出格式不符合要求。"
    "请在 Dify 中检查「结构化输出」节点配置，或关闭模型的思考/推理输出。"
)
MSG_THINKING = "正在思考..."


def format_dify_error_for_user(error: str | None) -> str:
    if not error:
        return MSG_DIFY_ERROR
    lower = error.lower()
    if "structured output" in lower or "parse structured" in lower:
        return MSG_DIFY_STRUCTURED_OUTPUT
    if len(error) > 150 or "redacted_thinking" in lower:
        return MSG_DIFY_ERROR
    return f"处理失败：{error}"


def truncate_utf8(text: str, max_bytes: int = MAX_CARD_BYTES) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text

    suffix_bytes = TRUNCATE_SUFFIX.encode("utf-8")
    limit = max_bytes - len(suffix_bytes)
    if limit <= 0:
        return TRUNCATE_SUFFIX[:max_bytes]

    truncated = encoded[:limit]
    while truncated and (truncated[-1] & 0xC0) == 0x80:
        truncated = truncated[:-1]
    return truncated.decode("utf-8", errors="ignore") + TRUNCATE_SUFFIX


def parse_from_event_dict(event: dict[str, Any]) -> FeishuIncomingMessage | None:
    """Parse im.message.receive_v1 event body dict."""
    sender_raw = event.get("sender") or {}
    message_raw = event.get("message") or {}

    sender = FeishuSender.model_validate(sender_raw)
    message = FeishuMessageBody.model_validate(message_raw)

    if not message.message_id:
        return None

    return FeishuIncomingMessage(
        message_id=message.message_id,
        chat_id=message.chat_id,
        chat_type=message.chat_type,
        message_type=message.message_type,
        content=message.content,
        open_id=sender.sender_id.open_id,
        user_id=sender.sender_id.user_id,
        sender_type=sender.sender_type,
    )


def parse_from_lark_event(data: Any) -> FeishuIncomingMessage | None:
    """Parse lark-oapi P2ImMessageReceiveV1 event object."""
    event = getattr(data, "event", None)
    if event is None:
        return None

    sender = getattr(event, "sender", None)
    message = getattr(event, "message", None)
    if message is None:
        return None

    sender_id = getattr(sender, "sender_id", None) if sender else None
    open_id = getattr(sender_id, "open_id", "") if sender_id else ""
    user_id = getattr(sender_id, "user_id", "") if sender_id else ""
    sender_type = getattr(sender, "sender_type", "user") if sender else "user"

    message_id = getattr(message, "message_id", "") or ""
    if not message_id:
        return None

    return FeishuIncomingMessage(
        message_id=message_id,
        chat_id=getattr(message, "chat_id", "") or "",
        chat_type=getattr(message, "chat_type", "p2p") or "p2p",
        message_type=getattr(message, "message_type", "") or "",
        content=getattr(message, "content", "") or "",
        open_id=open_id or "",
        user_id=user_id or "",
        sender_type=sender_type or "user",
    )


def extract_user_text(message: FeishuIncomingMessage) -> str | None:
    if message.message_type != "text":
        return None
    if not message.content:
        return None
    try:
        payload = json.loads(message.content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    text = payload.get("text")
    if not isinstance(text, str):
        return None
    content = text.strip()
    if not content:
        return None
    content = re.sub(r"^@_user_\S+\s*", "", content).strip()
    return content or None


def build_dify_user_id(message: FeishuIncomingMessage) -> str:
    user = message.open_id or message.user_id or "unknown"
    chat = message.chat_id or "single"
    return f"feishu_{user}_{chat}"


def log_incoming_user(message: FeishuIncomingMessage, *, query: str | None = None) -> None:
    query_text = query or ""
    if len(query_text) > 120:
        query_preview = query_text[:120] + "..."
    else:
        query_preview = query_text or "-"

    user_logger.info(
        "[Feishu用户] open_id={} | user_id={} | chat_id={} | chat_type={} | message_id={} | query={}",
        message.open_id or "-",
        message.user_id or "-",
        message.chat_id or "-",
        message.chat_type,
        message.message_id,
        query_preview,
    )
