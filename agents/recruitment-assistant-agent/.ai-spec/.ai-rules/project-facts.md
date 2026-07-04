# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: fe31471fffd80bf8
- last refresh: 2026-07-04 21:11:16 +08:00
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

- No common framework or tool detected from package.json.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
recruitment-assistant-agent/
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
| 当前阶段 | DESIGN-002 模块详细设计对齐 | 父目录 `docs/plans/current.md` | 已确认 |
| 下一步 | 确认材料格式、评分、公平性、保留和验收样本 | 父目录模块计划 | 已确认 |

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
