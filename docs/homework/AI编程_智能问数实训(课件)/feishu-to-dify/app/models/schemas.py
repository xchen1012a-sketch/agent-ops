"""Pydantic models for internal payloads."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FeishuSenderId(BaseModel):
    open_id: str = ""
    user_id: str = ""
    union_id: str = ""


class FeishuSender(BaseModel):
    sender_id: FeishuSenderId = Field(default_factory=FeishuSenderId)
    sender_type: str = "user"
    tenant_key: str = ""


class FeishuMessageBody(BaseModel):
    message_id: str = ""
    chat_id: str = ""
    chat_type: str = "p2p"
    message_type: str = ""
    content: str = ""


class FeishuIncomingMessage(BaseModel):
    """Normalized Feishu im.message.receive_v1 payload."""

    message_id: str
    chat_id: str
    chat_type: str = "p2p"
    message_type: str
    content: str = ""
    open_id: str = ""
    user_id: str = ""
    sender_type: str = "user"

    @property
    def session_key(self) -> str:
        return f"{self.open_id or self.user_id}:{self.chat_id}"

    @property
    def is_from_bot(self) -> bool:
        return self.sender_type == "app"


class CardStreamSession(BaseModel):
    card_id: str
    element_id: str = "markdown_1"
    sequence: int = 0

    def next_sequence(self) -> int:
        self.sequence += 1
        return self.sequence


class DifyStreamEvent(BaseModel):
    event: str
    task_id: str | None = None
    workflow_run_id: str | None = None
    data: dict[str, Any] | str | None = None
