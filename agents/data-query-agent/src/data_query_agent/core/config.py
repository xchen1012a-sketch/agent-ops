"""Typed application settings via Pydantic Settings v2."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_local_env_defaults() -> None:
    """Load the module .env into process env when pydantic does not pre-load it."""
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class Settings(BaseSettings):
    """All runtime configuration. Single source of truth."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["dev", "staging", "prod"] = "dev"
    app_name: str = "data-query-agent"
    app_port: int = 8103
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    # Auth
    jwt_secret: SecretStr = Field(default=SecretStr(""))
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 604800

    # Rate limit
    rate_limit_login_per_minute: int = 5
    rate_limit_api_per_minute: int = 60

    # Database (agent runtime, read-write)
    database_url: str = ""
    database_migration_url: str = ""
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_recycle_seconds: int = 3600
    database_slow_query_seconds: int = 5

    # Shop DB (read-only business database)
    shop_db_read_url: str = ""
    shop_db_read_only: bool = True
    shop_db_pool_size: int = 5
    shop_db_max_overflow: int = 10
    sql_execution_timeout_seconds: int = 10

    # Redis
    redis_url: str = ""

    # DeepSeek
    deepseek_api_base: str = ""
    deepseek_api_key: SecretStr = Field(default=SecretStr(""))
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: int = 60
    deepseek_max_retries: int = 3
    deepseek_backoff_seconds: str = "1,2,4"

    # SQL safety
    sql_whitelist_path: str = "/app/data/rules/sql-whitelist.yaml"
    indicators_path: str = "/app/data/rules/indicators.yaml"
    sql_max_rows: int = 1000
    sql_max_fields: int = 50
    sql_max_bytes: int = 1_048_576
    sql_audit_retention_days: int = 90
    mcp_server_url: str = ""
    mcp_timeout_seconds: int = 30
    feishu_enabled: bool = False

    # Agent API config center (CONFIG-100): Fernet master key for encrypting
    # upstream API keys stored in agent_api_config.api_key_encrypted.
    agent_config_encryption_key: SecretStr = Field(default=SecretStr(""))

    def validate_required(self) -> None:
        """Hard fail on missing critical secrets. Called from lifespan."""
        errors: list[str] = []
        if len(self.jwt_secret.get_secret_value()) < 32:
            errors.append("JWT_SECRET must be >= 32 bytes")
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        if not self.shop_db_read_url:
            errors.append("SHOP_DB_READ_URL is required")
        if not self.deepseek_api_key.get_secret_value():
            errors.append("DEEPSEEK_API_KEY is required")
        if not self.redis_url:
            errors.append("REDIS_URL is required")
        if not self.deepseek_api_base:
            errors.append("DEEPSEEK_API_BASE is required")
        if errors:
            raise RuntimeError("Configuration validation failed: " + "; ".join(errors))

    @model_validator(mode="after")
    def _validate_env(self) -> Settings:
        if self.app_env == "prod" and self.log_format != "json":
            raise ValueError("LOG_FORMAT must be json in prod")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a singleton Settings instance."""
    _load_local_env_defaults()
    return Settings()
