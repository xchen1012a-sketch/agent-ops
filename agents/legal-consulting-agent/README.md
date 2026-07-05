# legal-consulting-agent

Legal consulting agent built on FastAPI + LangGraph + DeepSeek `deepseek-chat`.

## Status

- Phase: FOUND-010 (engineering foundation)
- Real source: `docs/specification.md`, `docs/detailed-design.md`
- Decisions: `agent-suite-ops/docs/adr/0007-unified-auth.md`, `0008-legal-knowledge-source.md`, `0011-deployment-and-database-permissions.md`

## Directory layout

```text
src/legal_consulting_agent/
  main.py                    FastAPI app entry, lifespan, middleware
  core/
    config.py                Pydantic Settings
    errors.py                Domain error types and envelope
    logging.py               loguru structured JSON logging
  api/
    dependencies.py          FastAPI dependency providers
    v1/
      router.py              Versioned router aggregation
      endpoints/health.py    /health/live and /health/ready
  infrastructure/db/
    base.py                  SQLAlchemy declarative Base and metadata
    session.py               Async engine and session factory
  workflows/
    factory.py               LangGraph factory entrypoint (placeholder)
    state.py                 Base workflow state schema
migrations/                  Alembic versions
tests/                       Unit + integration tests
```

## Local development

Requirements: Python 3.12, MySQL 8, Redis 7.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -e ".[dev]"
cp .env.example .env            # then fill real values
alembic upgrade head
uvicorn legal_consulting_agent.main:app --reload --port 8101
```

## Health checks

- `GET /v1/health/live` - process alive (also mounted at `/api/legal/v1/health/live` for gateway routing)
- `GET /v1/health/ready` - dependencies reachable (DB, Redis, Embedding)

## Quality gates

```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest --cov=legal_consulting_agent
```

All commands must pass before merge.

## 验证状态（FOUND-010）

工程基线（端口 8101）：

- [x] Ruff check + format 全绿（0 errors）
- [x] MyPy strict 全绿
- [x] Pytest 覆盖率 83%（>= 80% 阈值）
- [x] Alembic 基线迁移 `0001_initial_baseline` 单一 head，离线 upgrade/downgrade 通过
- [x] Docker 镜像构建 + 独立运行成功（python:3.12-slim，非 root UID 1001，tini PID 1，HEALTHCHECK 路径 `/v1/health/live`，docker inspect `State.Health.Status = healthy`）
- [x] `.env.example` 仅占位值，启动校验 `JWT_SECRET >= 32 bytes`、`REDIS_URL`、`DEEPSEEK_API_BASE`、`EMBEDDING_BASE_URL`、`RAG_VECTOR_DB_URL`、`RAG_RERANKER_BASE_URL` 等关键配置；缺失时 `lifespan` 抛 `RuntimeError` 进程退出
- [x] pip-audit（OSV 数据源）：asyncmy 0.2.11 PYSEC-2026-286、ecdsa 0.19.2 CVE-2024-23342 — 见下方风险登记

未验证 / 待后续阶段：

- [ ] 真实 DeepSeek API 接入（LEGAL-100）
- [ ] LangGraph 业务节点（LEGAL-110）
- [ ] 法律知识库样本（待用户供给）

### 已知漏洞与处理

| 漏洞 | 来源 | 处理 |
|---|---|---|
| asyncmy 0.2.11 (PYSEC-2026-286) | 直接依赖 | 上游无 fix；MySQL 最小权限账号缓解（ADR-0011），监控上游 |
| ecdsa 0.19.2 (CVE-2024-23342) | python-jose 间接依赖 | 当前未实际调用 JWT；LEGAL-100 评估切换 PyJWT 或限制算法至 HS256/RS256 |
