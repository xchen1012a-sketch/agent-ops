"""Unit tests for typed Settings validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from data_query_agent.core.config import Settings


def test_settings_defaults_to_dev_env() -> None:
    settings = Settings(
        jwt_secret="x" * 32,
        database_url="mysql+asyncmy://u:p@mysql:3306/db",
        shop_db_read_url="mysql+asyncmy://u:p@mysql:3306/shop_db",
        deepseek_api_key="sk-test",
    )
    assert settings.app_env == "dev"
    assert settings.app_port == 8103
    assert settings.log_format == "json"


def test_settings_prod_requires_json_log_format() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env="prod",
            log_format="text",
            jwt_secret="x" * 32,
            database_url="mysql+asyncmy://u:p@mysql:3306/db",
            shop_db_read_url="mysql+asyncmy://u:p@mysql:3306/shop_db",
            deepseek_api_key="sk-test",
        )
    assert "LOG_FORMAT must be json in prod" in str(exc_info.value)


def test_validate_required_fails_on_short_jwt_secret() -> None:
    settings = Settings(
        jwt_secret="short",
        database_url="mysql+asyncmy://u:p@mysql:3306/db",
        shop_db_read_url="mysql+asyncmy://u:p@mysql:3306/shop_db",
        deepseek_api_key="sk-test",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_required()
    assert "JWT_SECRET" in str(exc_info.value)


def test_validate_required_fails_on_missing_database_url() -> None:
    settings = Settings(
        jwt_secret="x" * 32,
        database_url="",
        shop_db_read_url="mysql+asyncmy://u:p@mysql:3306/shop_db",
        deepseek_api_key="sk-test",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_required()
    assert "DATABASE_URL" in str(exc_info.value)


def test_validate_required_fails_on_missing_shop_db_read_url() -> None:
    settings = Settings(
        jwt_secret="x" * 32,
        database_url="mysql+asyncmy://u:p@mysql:3306/db",
        shop_db_read_url="",
        deepseek_api_key="sk-test",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_required()
    assert "SHOP_DB_READ_URL" in str(exc_info.value)


def test_validate_required_fails_on_missing_deepseek_key() -> None:
    settings = Settings(
        jwt_secret="x" * 32,
        database_url="mysql+asyncmy://u:p@mysql:3306/db",
        shop_db_read_url="mysql+asyncmy://u:p@mysql:3306/shop_db",
        deepseek_api_key="",
    )
    with pytest.raises(RuntimeError) as exc_info:
        settings.validate_required()
    assert "DEEPSEEK_API_KEY" in str(exc_info.value)


def _base_settings(**overrides: object) -> Settings:
    kwargs: dict[str, object] = {
        "jwt_secret": "x" * 32,
        "database_url": "mysql+asyncmy://u:p@mysql:3306/db",
        "shop_db_read_url": "mysql+asyncmy://u:p@mysql:3306/shop_db",
        "deepseek_api_key": "sk-test",
        "deepseek_api_base": "https://api.deepseek.com",
        "redis_url": "redis://redis:6379/0",
    }
    kwargs.update(overrides)
    return Settings(**kwargs)


def test_validate_required_skips_feishu_when_disabled() -> None:
    settings = _base_settings(feishu_enabled=False)
    settings.validate_required()


def test_validate_required_ignores_feishu_credentials_when_enabled() -> None:
    # FEISHU-300: 飞书凭证改为从 agent_api_config 表读取，启动期不再校验。
    settings = _base_settings(feishu_enabled=True)
    settings.validate_required()
