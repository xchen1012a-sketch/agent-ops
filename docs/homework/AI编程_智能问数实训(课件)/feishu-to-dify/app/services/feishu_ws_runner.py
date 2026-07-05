"""Feishu long-connection runner using lark-oapi WebSocket client."""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from app.config import Settings
from app.services.bridge import MessageBridge
from app.services.feishu_message import parse_from_lark_event
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FeishuWsRunner:
    """Maintain Feishu WebSocket long connection and route events to MessageBridge."""

    def __init__(
        self,
        settings: Settings,
        bridge: MessageBridge,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._settings = settings
        self._bridge = bridge
        self._loop = loop
        self._thread: threading.Thread | None = None
        self._client: Any = None
        self._stop_event = threading.Event()

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        return self._loop

    def _dispatch_message(self, data: Any) -> None:
        message = parse_from_lark_event(data)
        if message is None:
            logger.warning("failed to parse feishu message event")
            return

        loop = self._loop
        if loop is None:
            logger.error("event loop not set; dropping message_id={}", message.message_id)
            return

        asyncio.run_coroutine_threadsafe(
            self._bridge.handle_ws_message(message),
            loop,
        )

    def _build_event_handler(self) -> Any:
        import lark_oapi as lark

        def on_message_receive(data: Any) -> None:
            try:
                self._dispatch_message(data)
            except Exception:
                logger.exception("feishu message handler error")

        return (
            lark.EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(on_message_receive)
            .build()
        )

    def _run_client(self) -> None:
        import lark_oapi as lark

        event_handler = self._build_event_handler()
        self._client = lark.ws.Client(
            self._settings.feishu_app_id,
            self._settings.feishu_app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO,
        )
        logger.info("feishu websocket connecting app_id={}", self._settings.feishu_app_id)
        try:
            self._client.start()
        except Exception:
            if not self._stop_event.is_set():
                logger.exception("feishu websocket client exited with error")
        finally:
            logger.info("feishu websocket client stopped")

    async def start(self) -> None:
        self._ensure_loop()
        if not self._settings.feishu_app_id or not self._settings.feishu_app_secret:
            from app.config import ENV_FILE

            raise ValueError(
                "WebSocket mode requires FEISHU_APP_ID and FEISHU_APP_SECRET. "
                f"Check {ENV_FILE} exists and variables are set."
            )

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_client,
            name="feishu-ws",
            daemon=True,
        )
        self._thread.start()
        logger.info("feishu websocket runner thread started")

    async def stop(self) -> None:
        self._stop_event.set()
        client = self._client
        if client is not None:
            stop_fn = getattr(client, "stop", None)
            if callable(stop_fn):
                try:
                    stop_fn()
                except Exception:
                    logger.warning("feishu websocket stop raised", exc_info=True)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._thread = None
        self._client = None
        logger.info("feishu websocket runner stopped")
