"""Service settings loaded from environment."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AUTH_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_port: int = 8081
    jwt_secret: str = Field(default="dev-secret-change-me-in-production")
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 7
    cookie_name: str = "agent_suite_refresh"
    cookie_domain: str = ""
    allowed_origin: str = "http://localhost:5173"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
