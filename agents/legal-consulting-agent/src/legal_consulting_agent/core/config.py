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
    app_name: str = "legal-consulting-agent"
    app_port: int = 8101
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
    redis_url: str = ""

    # DeepSeek
    deepseek_api_base: str = ""
    deepseek_api_key: SecretStr = Field(default=SecretStr(""))
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: int = 60
    deepseek_max_retries: int = 3
    deepseek_backoff_seconds: str = "1,2,4"

    # Legal KB & RAG (hybrid retrieval per ADR-0012)
    legal_kb_path: str = "/app/data/legal_kb"
    high_risk_keywords_path: str = "/app/data/legal_kb/high-risk-keywords.yaml"

    # Embedding (BGE-M3 dense + sparse via HuggingFace TEI)
    embedding_base_url: str = ""
    embedding_model: str = "BAAI/bge-m3"

    # Vector store (Qdrant)
    rag_vector_db_url: str = ""
    rag_vector_collection: str = "legal_kb"

    # Hybrid retrieval weights and bounds
    rag_dense_weight: float = 0.7
    rag_sparse_weight: float = 0.3
    rag_recall_top_n: int = 20
    rag_rerank_top_n: int = 5
    rag_similarity_threshold: float = 0.65
    rag_category_filter_enabled: bool = True

    # Cross-encoder reranker
    rag_reranker_enabled: bool = True
    rag_reranker_base_url: str = ""
    rag_reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Backwards-compatible alias for legacy callers expecting top_k.
    @property
    def rag_top_k(self) -> int:
        return self.rag_rerank_top_n

    def validate_required(self) -> None:
        """Hard fail on missing critical secrets. Called from lifespan."""
        errors: list[str] = []
        if len(self.jwt_secret.get_secret_value()) < 32:
            errors.append("JWT_SECRET must be >= 32 bytes")
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        if not self.deepseek_api_key.get_secret_value():
            errors.append("DEEPSEEK_API_KEY is required")
        if not self.redis_url:
            errors.append("REDIS_URL is required")
        if not self.deepseek_api_base:
            errors.append("DEEPSEEK_API_BASE is required")
        if not self.embedding_base_url:
            errors.append("EMBEDDING_BASE_URL is required")
        if not self.rag_vector_db_url:
            errors.append("RAG_VECTOR_DB_URL is required")
        if not self.rag_reranker_base_url:
            errors.append("RAG_RERANKER_BASE_URL is required")
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
