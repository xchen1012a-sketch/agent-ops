# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: d57ec15539527d74
- last refresh: 2026-07-05 10:53:47 +0800
- refresh command: scripts/refresh-project-facts.sh

## [auto] Tech stack

- No package.json parser available.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
legal-consulting-agent/
|-- .coverage
|-- .env.example
|-- .gitignore
|-- .mypy_cache
|   |-- .mypy_cache/.gitignore
|   |-- .mypy_cache/3.12
|   |-- .mypy_cache/CACHEDIR.TAG
|-- .pytest_cache
|   |-- .pytest_cache/.gitignore
|   |-- .pytest_cache/CACHEDIR.TAG
|   |-- .pytest_cache/README.md
|   |-- .pytest_cache/v
|-- .ruff_cache
|   |-- .ruff_cache/.gitignore
|   |-- .ruff_cache/0.15.20
|   |-- .ruff_cache/CACHEDIR.TAG
|-- .uv-cache
|   |-- .uv-cache/.gitignore
|   |-- .uv-cache/.lock
|   |-- .uv-cache/CACHEDIR.TAG
|   |-- .uv-cache/interpreter-v4
|   |-- .uv-cache/sdists-v9
|-- .venv
|   |-- .venv/.gitignore
|   |-- .venv/.lock
|   |-- .venv/CACHEDIR.TAG
|   |-- .venv/Lib
|   |-- .venv/Scripts
|   |-- .venv/include
|   |-- .venv/pyvenv.cfg
|   |-- .venv/share
|-- AGENTS.md
|-- CLAUDE.md
|-- Dockerfile
|-- README.md
|-- alembic.ini
|-- docs
|   |-- docs/api-contract.md
|   |-- docs/architecture.md
|   |-- docs/detailed-design.md
|   |-- docs/specification.md
|-- migrations
|   |-- migrations/__pycache__
|   |-- migrations/env.py
|   |-- migrations/script.py.mako
|   |-- migrations/versions
|-- pyproject.toml
|-- scripts
|   |-- scripts/.gitkeep
|-- src
|   |-- src/legal_consulting_agent
|-- tests
|   |-- tests/__init__.py
|   |-- tests/__pycache__
|   |-- tests/conftest.py
|   |-- tests/contract
|   |-- tests/e2e
|   |-- tests/evaluation
|   |-- tests/integration
|   |-- tests/unit
|-- uv.lock
```

## [auto] Environment keys

- APP_ENV
- APP_NAME
- APP_PORT
- DATABASE_MAX_OVERFLOW
- DATABASE_MIGRATION_URL
- DATABASE_POOL_RECYCLE_SECONDS
- DATABASE_POOL_SIZE
- DATABASE_SLOW_QUERY_SECONDS
- DATABASE_URL
- DEEPSEEK_API_BASE
- DEEPSEEK_API_KEY
- DEEPSEEK_BACKOFF_SECONDS
- DEEPSEEK_MAX_RETRIES
- DEEPSEEK_MODEL
- DEEPSEEK_TIMEOUT_SECONDS
- EMBEDDING_BASE_URL
- EMBEDDING_MODEL
- HIGH_RISK_KEYWORDS_PATH
- JWT_ACCESS_TTL_SECONDS
- JWT_REFRESH_TTL_SECONDS
- JWT_SECRET
- LEGAL_KB_PATH
- LOG_FORMAT
- LOG_LEVEL
- RAG_CATEGORY_FILTER_ENABLED
- RAG_DENSE_WEIGHT
- RAG_RECALL_TOP_N
- RAG_RERANKER_BASE_URL
- RAG_RERANKER_ENABLED
- RAG_RERANKER_MODEL
- RAG_RERANK_TOP_N
- RAG_SIMILARITY_THRESHOLD
- RAG_SPARSE_WEIGHT
- RAG_VECTOR_COLLECTION
- RAG_VECTOR_DB_URL
- RATE_LIMIT_API_PER_MINUTE
- RATE_LIMIT_LOGIN_PER_MINUTE
- REDIS_URL

## [auto] Git status

- Current branch: main
- Working tree: has uncommitted changes
- Remotes:
  - origin	https://github.com/xchen1012a-sketch/agent-ops.git (fetch)
  - origin	https://github.com/xchen1012a-sketch/agent-ops.git (push)
<!-- ai-facts:auto:end -->

<!-- ai-facts:manual:start -->
## [manual] 项目身份

| 字段 | 值 | 来源 | 状态 |
|---|---|---|---|
| 项目名称 | legal-consulting-agent | 用户确认 + 总体计划 | 已确认 |
| 产品定位 | 独立法律咨询 Agent API | `docs/specification.md` | 已确认 |
| 业务域 | 法律分类、咨询会话、知识检索、回答与报告 | `docs/specification.md` | 已确认 |
| 仓库/子仓命名 | agents/legal-consulting-agent | 用户确认 | 已确认 |

## [manual] 模块词表

| 模块 | 说明 | 命名前缀/目录 | 来源 | 状态 |
|---|---|---|---|---|
| frontend |  |  |  | 待确认 |
| backend | FastAPI + LangGraph + DeepSeek deepseek-chat | `src/`（FOUND-010 创建） | 用户确认 + 总体计划 | 已确认 |
| database | MySQL 8 + SQLAlchemy 2 + Alembic | `migrations/`（后续创建） | `legal_agent_db`，总体计划 | 已确认 |
| ops |  |  |  | 待确认 |

## [manual] 阶段前缀

| 前缀 | 含义 | 来源 | 状态 |
|---|---|---|---|
| FE |  |  | 待确认 |
| BE |  |  | 待确认 |
| DB |  |  | 待确认 |
| OPS |  |  | 待确认 |

## [manual] 当前阶段

| 字段 | 值 | 来源 | 状态 |
|---|---|---|---|
| 当前阶段 | LEGAL-100 法律咨询 Agent 业务实现 | 父目录 `docs/plans/current.md` | 已确认 |
| 下一步 | 继续 `LEGAL-130` 后续表；RAG、知识库索引和真实 DeepSeek 调用后置到 `LEGAL-140` | 父目录 `docs/plans/current.md` + `docs/plans/phases/LEGAL-100-legal-consulting-agent.md` | 已确认 |

## [manual] 外部服务

| 服务 | 用途/边界 | 来源 | 状态 |
|---|---|---|---|
| 数据库 | MySQL 8 / legal_agent_db | 总体计划 | 已确认 |
| Redis |  |  | 待确认 |
| AI 服务 | DeepSeek 官方 API / deepseek-chat | 用户确认 | 已确认 |
| 对象存储 |  |  | 待确认 |

## [manual] 生成与禁改路径

| 类型 | 路径 | 规则 | 来源 | 状态 |
|---|---|---|---|---|
| 自动生成目录 |  | 不手改；通过生成命令更新 |  | 待确认 |
| 禁止手改目录 |  | 只读或先确认 |  | 待确认 |
| 只能命令生成 |  | 记录生成命令 |  | 待确认 |

## [manual] 安全边界

| 边界 | 规则 | 来源 | 状态 |
|---|---|---|---|
| 不接真实生产服务 | 未经确认不连接真实用户、法律材料或生产服务 | 项目红线 | 已确认 |
| 不执行危险命令 | 不执行LLM生成命令/路径，不自动提交或推送 | 项目红线 | 已确认 |
<!-- ai-facts:manual:end -->
