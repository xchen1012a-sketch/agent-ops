"""Production Feishu event webhook route: fast-ack, then answer asynchronously.

飞书对外回调端点。安全边界（验签/解密/token/去重）在 application 层完成；本层只做协议：
读原始 body、取签名头、挑战原样回、消息秒回 200 并交后台异步回推——飞书要求 3s 内响应，
工作流耗时较长，必须异步。

注意（有意为之）：本端点响应不套内部 ``{data, error}`` Envelope，而是遵循飞书回调契约
（challenge 原样回、事件回 ``{"code": 0}``），与自有前端接口的响应约定不同。
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Request

from data_query_agent.api.dependencies import FeishuWebhookDepsDep
from data_query_agent.core.errors import NotFoundError

router = APIRouter()


@router.post("/integrations/feishu/webhook")
async def handle_feishu_webhook(
    request: Request,
    background: BackgroundTasks,
    deps: FeishuWebhookDepsDep,
) -> dict[str, object]:
    """Handle a Feishu event: fast-ack challenges/messages, answer asynchronously."""
    if not deps.enabled or deps.processor is None or deps.dispatch is None:
        raise NotFoundError("feishu integration disabled")
    raw_body = await request.body()
    result = await deps.processor.process(
        raw_body=raw_body,
        timestamp=request.headers.get("X-Lark-Request-Timestamp"),
        nonce=request.headers.get("X-Lark-Request-Nonce"),
        signature=request.headers.get("X-Lark-Signature"),
    )
    if result.challenge is not None:
        return {"challenge": result.challenge}
    if result.message is not None:
        background.add_task(deps.dispatch, result.message)
    return {"code": 0}
