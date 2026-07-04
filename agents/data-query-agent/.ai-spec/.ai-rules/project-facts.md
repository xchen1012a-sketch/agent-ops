# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: 29ba04f9c7415793
- last refresh: 2026-07-04 21:11:16 +08:00
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

- No common framework or tool detected from package.json.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
data-query-agent/
|-- docs/
|   |-- api-contract.md
|   |-- architecture.md
|   |-- specification.md
|-- .gitignore
|-- AGENTS.md
|-- CLAUDE.md
|-- README.md
```

## [auto] Environment keys

- No .env*.example keys detected.

## [auto] Git status

- Git status check failed: fatal: not a git repository (or any of the parent directories): .git
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
| 当前阶段 | DESIGN-002 模块详细设计对齐 | 父目录 `docs/plans/current.md` | 已确认 |
| 下一步 | 固化MCP、指标字典、SQL策略、评测与飞书边界 | 父目录模块计划 | 已确认 |

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
