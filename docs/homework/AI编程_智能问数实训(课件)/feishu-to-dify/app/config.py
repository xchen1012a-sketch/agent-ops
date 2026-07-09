"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    feishu_mode: Literal["websocket", "webhook"] = Field(
        default="websocket",
        alias="FEISHU_MODE",
    )

    feishu_app_id: str = Field(default="", alias="FEISHU_APP_ID")
    feishu_app_secret: str = Field(default="", alias="FEISHU_APP_SECRET")

    # Webhook mode only (future)
    feishu_verification_token: str = Field(default="", alias="FEISHU_VERIFICATION_TOKEN")
    feishu_encrypt_key: str = Field(default="", alias="FEISHU_ENCRYPT_KEY")

    dify_api_base: str = Field(
        default="http://localhost/v1",
        alias="DIFY_API_BASE",
    )
    dify_api_key: str = Field(default="", alias="DIFY_API_KEY")
    dify_input_key: str = Field(default="query", alias="DIFY_INPUT_KEY")
    dify_timeout: float = Field(default=120.0, alias="DIFY_TIMEOUT")

    msg_dedup_ttl: int = Field(default=600, alias="MSG_DEDUP_TTL")
    ws_stream_push_interval: float = Field(default=1.0, alias="WS_STREAM_PUSH_INTERVAL")

    welcome_message: str = Field(
        default="你好，我是智能助手，有什么可以帮你的？",
        alias="WELCOME_MESSAGE",
    )

    feishu_api_base: str = Field(
        default="https://open.feishu.cn",
        alias="FEISHU_API_BASE",
    )

    @property
    def dify_workflow_run_url(self) -> str:
        base = self.dify_api_base.rstrip("/")
        return f"{base}/workflows/run"

    @property
    def uses_websocket(self) -> bool:
        return self.feishu_mode == "websocket"

    @property
    def uses_webhook(self) -> bool:
        return self.feishu_mode == "webhook"


@lru_cache
def get_settings() -> Settings:
    return Settings()
