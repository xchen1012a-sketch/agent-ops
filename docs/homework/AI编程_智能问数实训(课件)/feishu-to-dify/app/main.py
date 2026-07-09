"""FastAPI application entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.services.bridge import MessageBridge
from app.services.feishu_ws_runner import FeishuWsRunner
from app.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

_ws_runner: FeishuWsRunner | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _ws_runner

    settings = get_settings()
    setup_logging(settings.log_level)

    if settings.uses_websocket:
        bridge = MessageBridge(settings)
        _ws_runner = FeishuWsRunner(settings, bridge)
        await _ws_runner.start()
        logger.info("started in Feishu WebSocket (long connection) mode")
    elif settings.uses_webhook:
        from app.api.feishu import router as feishu_router

        _app.include_router(feishu_router)
        logger.info("started in Feishu Webhook mode (stub; not yet implemented)")
    else:
        logger.warning("unknown FEISHU_MODE={}", settings.feishu_mode)

    yield

    if _ws_runner is not None:
        await _ws_runner.stop()


app = FastAPI(
    title="feishu-to-dify",
    description="飞书应用机器人与 Dify 工作流对接中间层",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "feishu_mode": settings.feishu_mode,
    }


def main() -> None:
    import uvicorn

    settings = get_settings()
    setup_logging(settings.log_level)
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
