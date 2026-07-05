"""Typed application settings via Pydantic Settings v2."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    app_name: str = "recruitment-assistant-agent"
    app_port: int = 8102
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    # Auth
    jwt_secret: SecretStr = Field(default=SecretStr(""))
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 604800

    # Rate limit
    rate_limit_login_per_minute: int = 5
    rate_limit_api_per_minute: int = 60

    # Database
    database_url: str = ""
    database_migration_url: str = ""
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_recycle_seconds: int = 3600
    database_slow_query_seconds: int = 5

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # DeepSeek
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_api_key: SecretStr = Field(default=SecretStr(""))
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: int = 60
    deepseek_max_retries: int = 3
    deepseek_backoff_seconds: str = "1,2,4"

    # Recruitment inputs
    upload_path: str = "/app/data/uploads"
    scoring_rules_path: str = "/app/data/rules/scoring-rules.yaml"
    max_resume_size_mb: int = 10

    def validate_required(self) -> None:
        """Hard fail on missing critical secrets. Called from lifespan."""
        errors: list[str] = []
        if len(self.jwt_secret.get_secret_value()) < 32:
            errors.append("JWT_SECRET must be >= 32 bytes")
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        if not self.deepseek_api_key.get_secret_value():
            errors.append("DEEPSEEK_API_KEY is required")
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
    return Settings()
