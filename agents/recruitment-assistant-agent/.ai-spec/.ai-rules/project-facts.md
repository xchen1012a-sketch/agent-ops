# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: ea680b49675b6c3a
- last refresh: 2026-07-05 18:03:08 +08:00
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

- No common framework or tool detected from package.json.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
recruitment-assistant-agent/
|-- .mypy_cache/
|   |-- 3.12/
|   |-- .gitignore
|   |-- CACHEDIR.TAG
|-- .pytest_cache/
|   |-- v/
|   |-- .gitignore
|   |-- CACHEDIR.TAG
|   |-- README.md
|-- .ruff_cache/
|   |-- 0.15.20/
|   |-- .gitignore
|   |-- CACHEDIR.TAG
|-- .tmp/
|   |-- pytest/
|-- .uv-cache/
|   |-- interpreter-v4/
|   |-- sdists-v9/
|   |-- .gitignore
|   |-- .lock
|   |-- CACHEDIR.TAG
|-- .venv/
|   |-- include/
|   |-- Lib/
|   |-- Scripts/
|   |-- .gitignore
|   |-- .lock
|   |-- CACHEDIR.TAG
|   |-- pyvenv.cfg
|-- docs/
|   |-- api-contract.md
|   |-- architecture.md
|   |-- detailed-design.md
|   |-- specification.md
|-- migrations/
|   |-- __pycache__/
|   |-- versions/
|   |-- env.py
|   |-- script.py.mako
|-- scripts/
|   |-- .gitkeep
|-- src/
|   |-- recruitment_assistant_agent/
|-- tests/
|   |-- __pycache__/
|   |-- contract/
|   |-- e2e/
|   |-- evaluation/
|   |-- integration/
|   |-- unit/
|   |-- __init__.py
|   |-- conftest.py
|-- .coverage
|-- .env.example
|-- .gitignore
|-- AGENTS.md
|-- alembic.ini
|-- CLAUDE.md
|-- Dockerfile
|-- pyproject.toml
|-- README.md
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
- JWT_ACCESS_TTL_SECONDS
- JWT_REFRESH_TTL_SECONDS
- JWT_SECRET
- LOG_FORMAT
- LOG_LEVEL
- MAX_RESUME_SIZE_MB
- RATE_LIMIT_API_PER_MINUTE
- RATE_LIMIT_LOGIN_PER_MINUTE
- REDIS_URL
- SCORING_RULES_PATH
- UPLOAD_PATH

## [auto] Git status

- Current branch: legal-100-data-workflow-local
- Working tree: has uncommitted changes
- Remotes:
  - origin	https://github.com/xchen1012a-sketch/agent-ops.git (fetch)
  - origin	https://github.com/xchen1012a-sketch/agent-ops.git (push)
<!-- ai-facts:auto:end -->

<!-- ai-facts:manual:start -->
## [manual] 项目身份

| 字段 | 值 | 来源 | 状态 |
|---|---|---|---|
| 项目名称 | recruitment-assistant-agent | 用户确认 + 总体计划 | 已确认 |
| 产品定位 | 独立智能招聘辅助 Agent API | `docs/specification.md` | 已确认 |
| 业务域 | 简历/JD解析、证据匹配、差距、面试问题与报告 | `docs/specification.md` | 已确认 |
| 仓库/子仓命名 | agents/recruitment-assistant-agent | 用户确认 | 已确认 |

## [manual] 模块词表

| 模块 | 说明 | 命名前缀/目录 | 来源 | 状态 |
|---|---|---|---|---|
| frontend |  |  |  | 待确认 |
| backend | FastAPI + LangGraph + DeepSeek deepseek-chat | `src/`（FOUND-010 创建） | 用户确认 + 总体计划 | 已确认 |
| database | MySQL 8 + SQLAlchemy 2 + Alembic | `migrations/`（后续创建） | `recruitment_agent_db`，总体计划 | 已确认 |
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
| 当前阶段 | FOUND-010 企业级工程基础 | 父目录 `docs/plans/current.md` | 已确认 |
| 下一步 | 等待用户授权进入 RECRUIT-200；需先确认材料格式、评分、公平性、保留和验收样本 | 父目录 `docs/plans/current.md` + 父目录模块计划 | 已确认 |

## [manual] 外部服务

| 服务 | 用途/边界 | 来源 | 状态 |
|---|---|---|---|
| 数据库 | MySQL 8 / recruitment_agent_db | 总体计划 | 已确认 |
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
| 不接真实生产服务 | 未经确认不处理真实候选人材料或生产服务 | 项目红线 | 已确认 |
| 不执行危险命令 | 不执行LLM生成命令/路径，不自动提交或推送 | 项目红线 | 已确认 |
<!-- ai-facts:manual:end -->
