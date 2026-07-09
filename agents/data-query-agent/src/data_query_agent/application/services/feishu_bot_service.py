"""Application service: turn a Feishu inbound message into a workflow reply.

编排层。解析飞书 ``im.message.receive_v1`` 事件为领域输入，异步调用现有 data-query
工作流（不改动 agent 内部，仅 ``graph.invoke({"question": ...})``），把 ``answer`` 文本回推。
本服务不触碰数据库/HTTP 细节，可用替身离线测试。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast

from data_query_agent.core.errors import InputBlockedError
from data_query_agent.core.logging import get_logger
from data_query_agent.workflows.graph import create_data_query_graph

_UNSUPPORTED_REPLY = "目前只支持文本消息，请直接发送文字问题。"
_EMPTY_ANSWER_REPLY = "没有查到可回复的内容，请换个问法再试。"
_ERROR_REPLY = "处理你的问题时出错了，请稍后再试。"
_SUBJECT_PREFIX = "feishu:"

_logger = get_logger(__name__)


def feishu_subject(open_id: str) -> str:
    """Map a Feishu open_id to the external subject used for data isolation.

    每个飞书用户映射为唯一 subject，接入现有 ``external_subject`` 隔离链路，与 Web 端隔离一致。
    """
    return f"{_SUBJECT_PREFIX}{open_id}"


class FeishuMessageSender(Protocol):
    """Boundary for sending a text reply back to Feishu."""

    async def send_text(
        self, *, receive_id: str, text: str, receive_id_type: str = "open_id"
    ) -> None:
        """Send a plain-text message to a receiver."""


@dataclass(frozen=True, slots=True)
class FeishuInboundMessage:
    """Parsed Feishu message event fields required to answer and isolate."""

    open_id: str
    text: str
    message_type: str
    chat_id: str | None
    event_id: str | None


def parse_message_event(event: Mapping[str, Any]) -> FeishuInboundMessage:
    """Extract sender/text from a decrypted ``im.message.receive_v1`` event body.

    第三方结构视为不可信输入，逐层校验；缺少发送者 open_id 抛 ``InputBlockedError``。
    非文本消息保留 message_type，由上层决定回退提示，不在此处静默丢弃。
    """
    header = _as_mapping(event.get("header"))
    payload = _as_mapping(event.get("event"))
    message = _as_mapping(payload.get("message"))
    sender = _as_mapping(payload.get("sender"))
    sender_id = _as_mapping(sender.get("sender_id"))

    open_id = sender_id.get("open_id")
    if not isinstance(open_id, str) or not open_id.strip():
        raise InputBlockedError("Feishu message sender open_id is required")

    message_type = message.get("message_type")
    text = ""
    if message_type == "text":
        text = _extract_text(message.get("content"))

    chat_id = message.get("chat_id")
    event_id = header.get("event_id")
    return FeishuInboundMessage(
        open_id=open_id.strip(),
        text=text,
        message_type=str(message_type or ""),
        chat_id=chat_id if isinstance(chat_id, str) else None,
        event_id=event_id if isinstance(event_id, str) else None,
    )


class FeishuBotService:
    """Answer a parsed Feishu message via the data-query workflow."""

    def __init__(
        self,
        *,
        client: FeishuMessageSender,
        graph_factory: Callable[[], object] = create_data_query_graph,
    ) -> None:
        self._client = client
        self._graph_factory = graph_factory

    async def answer_message(self, message: FeishuInboundMessage) -> None:
        """Run the workflow for text messages and reply; guide non-text ones."""
        if message.message_type != "text" or not message.text:
            await self._client.send_text(receive_id=message.open_id, text=_UNSUPPORTED_REPLY)
            return
        try:
            answer = await self._run_workflow(message.text)
        except Exception as exc:
            # 后台任务里工作流失败若不兜底，用户会收到静默无回复；记录并回退提示文案。
            _logger.warning(
                "feishu.workflow_failed", open_id=message.open_id, error=str(exc)
            )
            answer = _ERROR_REPLY
        await self._client.send_text(
            receive_id=message.open_id, text=answer or _EMPTY_ANSWER_REPLY
        )

    async def _run_workflow(self, question: str) -> str:
        """Invoke the compiled graph off the event loop; return the answer text.

        ``graph.invoke`` 为同步阻塞调用，用 ``to_thread`` 避免阻塞事件循环。
        """

        def _invoke() -> str:
            graph = cast(Any, self._graph_factory())
            state = graph.invoke({"question": question})
            if isinstance(state, Mapping):
                return str(state.get("answer", ""))
            return ""

        return await asyncio.to_thread(_invoke)


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _extract_text(content: object) -> str:
    if not isinstance(content, str):
        return ""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise InputBlockedError("Feishu text message content is not valid JSON") from exc
    if isinstance(parsed, Mapping):
        text = parsed.get("text")
        if isinstance(text, str):
            return text.strip()
    return ""
