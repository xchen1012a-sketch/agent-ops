# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: ad02e758b2d2e064
- last refresh: 2026-07-05 14:06:31 +08:00
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

- No common framework or tool detected from package.json.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
data-query-agent/
|-- .mypy_cache/
|   |-- 3.12/
|   |-- .gitignore
|   |-- CACHEDIR.TAG
|-- .pytest_cache/
|-- .ruff_cache/
|   |-- 0.15.20/
|   |-- .gitignore
|   |-- CACHEDIR.TAG
|-- .venv/
|   |-- include/
|   |-- Lib/
|   |-- Scripts/
|   |-- share/
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
|   |-- versions/
|   |-- env.py
|   |-- script.py.mako
|-- scripts/
|   |-- .gitkeep
|-- src/
|   |-- data_query_agent/
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
- FEISHU_ENABLED
- INDICATORS_PATH
- JWT_ACCESS_TTL_SECONDS
- JWT_REFRESH_TTL_SECONDS
- JWT_SECRET
- LOG_FORMAT
- LOG_LEVEL
- MCP_SERVER_URL
- MCP_TIMEOUT_SECONDS
- RATE_LIMIT_API_PER_MINUTE
- RATE_LIMIT_LOGIN_PER_MINUTE
- REDIS_URL
- SHOP_DB_MAX_OVERFLOW
- SHOP_DB_POOL_SIZE
- SHOP_DB_READ_ONLY
- SHOP_DB_READ_URL
- SQL_AUDIT_RETENTION_DAYS
- SQL_EXECUTION_TIMEOUT_SECONDS
- SQL_MAX_BYTES
- SQL_MAX_FIELDS
- SQL_MAX_ROWS
- SQL_WHITELIST_PATH

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
| 项目名称 | data-query-agent | 用户确认 + 总体计划 | 已确认 |
| 产品定位 | 独立 NL2SQL 智能问数 Agent API，支持 Web 与飞书 | `docs/specification.md` | 已确认 |
| 业务域 | 电商数据字典、指标、SQL安全查询、解读与图表 | `docs/specification.md` | 已确认 |
| 仓库/子仓命名 | agents/data-query-agent | 用户确认 | 已确认 |

## [manual] 模块词表

| 模块 | 说明 | 命名前缀/目录 | 来源 | 状态 |
|---|---|---|---|---|
| frontend |  |  |  | 待确认 |
| backend | FastAPI + LangGraph + DeepSeek deepseek-chat | `src/`（FOUND-010 创建） | 用户确认 + 总体计划 | 已确认 |
| database | MySQL 8；shop_db只读 + data_query_agent_db运行态 | `migrations/`仅管理运行态库 | 课件 + 详细计划 | 已确认 |
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
| 下一步 | 等待用户授权进入 DATA-300；需先固化 MCP、指标字典、SQL 策略、评测与飞书边界 | 父目录 `docs/plans/current.md` + 父目录模块计划 | 已确认 |

## [manual] 外部服务

| 服务 | 用途/边界 | 来源 | 状态 |
|---|---|---|---|
| 数据库 | MySQL 8；shop_db只读，data_query_agent_db读写 | 详细计划 | 已确认 |
| Redis |  |  | 待确认 |
| AI 服务 | DeepSeek官方API/deepseek-chat；MySQL MCP查询主链路 | 用户确认 + 课件要求 | 已确认 |
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
| 不接真实生产服务 | 未经确认不连接生产数据库、飞书租户或真实业务数据 | 项目红线 | 已确认 |
| 不执行危险命令 | LLM SQL须经Schema与AST校验；不自动提交或推送 | 项目红线 | 已确认 |
<!-- ai-facts:manual:end -->
