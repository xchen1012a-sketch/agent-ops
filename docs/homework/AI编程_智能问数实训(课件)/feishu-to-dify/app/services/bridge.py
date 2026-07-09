"""Orchestrate Feishu events and Dify workflow streaming."""

from __future__ import annotations

import asyncio
import time
from typing import Protocol

import httpx

from app.config import Settings
from app.models.schemas import CardStreamSession, FeishuIncomingMessage
from app.services.dify_client import (
    DifyClientError,
    DifyWorkflowClient,
    extract_error_message,
    extract_text_chunk,
    is_human_input_event,
    parse_workflow_finished,
)
from app.services.feishu_api import FeishuApiClient, FeishuApiError
from app.services.feishu_card import FeishuCardStreamer
from app.services.feishu_message import (
    MSG_DIFY_ERROR,
    MSG_DIFY_TIMEOUT,
    MSG_DIFY_UNAVAILABLE,
    MSG_HUMAN_INPUT,
    MSG_THINKING,
    MSG_UNSUPPORTED,
    build_dify_user_id,
    extract_user_text,
    format_dify_error_for_user,
    log_incoming_user,
    truncate_utf8,
)
from app.utils.dedup import MessageDeduper
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CardStreamPusher(Protocol):
    async def start_stream(self, *, chat_id: str, placeholder: str = MSG_THINKING) -> CardStreamSession: ...

    async def push_content(self, session: CardStreamSession, content: str) -> None: ...

    async def finish(self, session: CardStreamSession, content: str) -> None: ...


class MessageBridge:
    def __init__(
        self,
        settings: Settings,
        *,
        deduper: MessageDeduper | None = None,
        dify_client: DifyWorkflowClient | None = None,
        feishu_api: FeishuApiClient | None = None,
        card_streamer: FeishuCardStreamer | None = None,
    ) -> None:
        self._settings = settings
        self._deduper = deduper or MessageDeduper(settings.msg_dedup_ttl)
        self._dify = dify_client or DifyWorkflowClient(settings)
        api = feishu_api or FeishuApiClient(settings)
        self._cards: CardStreamPusher = card_streamer or FeishuCardStreamer(api)
        self._tasks: set[asyncio.Task] = set()

    def _track_task(self, task: asyncio.Task) -> None:
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _finish_dify_stream(
        self,
        *,
        session: CardStreamSession,
        push,
        aggregated: str,
        finished,
        msgid: str,
        task_id: str | None,
    ) -> None:
        if finished.output:
            await push(finished.output, finish=True)
            logger.info(
                "dify finished message_id={} task_id={} len={}",
                msgid,
                task_id,
                len(finished.output),
            )
            return

        if aggregated:
            logger.warning(
                "dify workflow failed, using streamed content message_id={} task_id={} error={}",
                msgid,
                task_id,
                finished.error,
            )
            await push(aggregated, finish=True)
            return

        logger.error(
            "dify workflow failed message_id={} task_id={} error={}",
            msgid,
            task_id,
            finished.error,
        )
        await push(format_dify_error_for_user(finished.error), finish=True)

    async def handle_ws_message(self, message: FeishuIncomingMessage) -> None:
        """Handle im.message.receive_v1 from Feishu long connection."""
        if message.is_from_bot:
            logger.debug("ignore bot message message_id={}", message.message_id)
            return

        user_text = extract_user_text(message)
        log_incoming_user(message, query=user_text)

        if not self._deduper.try_acquire(message.message_id):
            logger.info("duplicate message_id={} ignored", message.message_id)
            return

        if message.message_type != "text":
            task = asyncio.create_task(self._reply_unsupported(message))
            self._track_task(task)
            return

        if not user_text:
            task = asyncio.create_task(self._reply_unsupported(message))
            self._track_task(task)
            return

        task = asyncio.create_task(
            self._run_message_pipeline(
                message=message,
                query=user_text,
            )
        )
        self._track_task(task)

    async def _reply_unsupported(self, message: FeishuIncomingMessage) -> None:
        try:
            session = await self._cards.start_stream(
                chat_id=message.chat_id,
                placeholder=MSG_UNSUPPORTED,
            )
            await self._cards.finish(session, MSG_UNSUPPORTED)
        except FeishuApiError:
            logger.exception(
                "failed to reply unsupported message_id={}",
                message.message_id,
            )

    async def _run_message_pipeline(
        self,
        *,
        message: FeishuIncomingMessage,
        query: str,
    ) -> None:
        msgid = message.message_id
        try:
            session = await self._cards.start_stream(
                chat_id=message.chat_id,
                placeholder=MSG_THINKING,
            )
        except FeishuApiError:
            logger.exception("failed to start card stream message_id={}", msgid)
            return

        await self._run_dify_pipeline_card(
            session=session,
            query=query,
            user=build_dify_user_id(message),
            msgid=msgid,
        )

    async def _run_dify_pipeline_card(
        self,
        *,
        session: CardStreamSession,
        query: str,
        user: str,
        msgid: str,
    ) -> None:
        aggregated = ""
        task_id: str | None = None
        last_push = 0.0
        interval = self._settings.ws_stream_push_interval

        async def push(content: str, *, finish: bool = False) -> None:
            nonlocal last_push
            safe = truncate_utf8(content)
            now = time.monotonic()
            if finish:
                await self._cards.finish(session, safe)
                last_push = now
                return
            if now - last_push >= interval:
                await self._cards.push_content(session, safe)
                last_push = now

        try:
            async for event in self._dify.run_stream(query, user):
                if event.task_id:
                    task_id = event.task_id

                if is_human_input_event(event):
                    await push(MSG_HUMAN_INPUT, finish=True)
                    return

                chunk = extract_text_chunk(event)
                if chunk:
                    aggregated += chunk
                    await push(aggregated, finish=False)

                finished = parse_workflow_finished(event)
                if finished is not None:
                    await self._finish_dify_stream(
                        session=session,
                        push=push,
                        aggregated=aggregated,
                        finished=finished,
                        msgid=msgid,
                        task_id=task_id,
                    )
                    return

                error_msg = extract_error_message(event)
                if error_msg:
                    raise DifyClientError(error_msg)

            if aggregated:
                await push(aggregated, finish=True)
            else:
                await push(MSG_DIFY_ERROR, finish=True)

        except asyncio.CancelledError:
            raise
        except httpx.TimeoutException:
            logger.exception("dify timeout message_id={} task_id={}", msgid, task_id)
            await push(MSG_DIFY_TIMEOUT, finish=True)
        except DifyClientError as exc:
            logger.error("dify error message_id={} task_id={}: {}", msgid, task_id, exc)
            if aggregated:
                await push(aggregated, finish=True)
            else:
                await push(format_dify_error_for_user(str(exc)), finish=True)
        except FeishuApiError:
            logger.exception("feishu card update error message_id={} task_id={}", msgid, task_id)
        except Exception:
            logger.exception("pipeline error message_id={} task_id={}", msgid, task_id)
            try:
                await push(MSG_DIFY_UNAVAILABLE, finish=True)
            except FeishuApiError:
                logger.exception("failed to send error card message_id={}", msgid)
