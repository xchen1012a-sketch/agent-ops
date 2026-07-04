# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: 1bd0306539636005
- last refresh: 2026-07-04 21:11:15 +08:00
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

- No common framework or tool detected from package.json.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
agent-suite-web/
|-- docs/
|   |-- api-integration.md
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
| 项目名称 | agent-suite-web | 用户确认 + `docs/plans/project-plan.md` | 已确认 |
| 产品定位 | 三个独立 Agent 的统一 Vue 3 Web 前端 | `docs/specification.md` | 已确认 |
| 业务域 | 法律咨询、智能招聘、智能问数的前端交互与展示 | `docs/specification.md` | 已确认 |
| 仓库/子仓命名 | agent-suite-web | 用户确认 | 已确认 |

## [manual] 模块词表

| 模块 | 说明 | 命名前缀/目录 | 来源 | 状态 |
|---|---|---|---|---|
| frontend | Vite + Vue 3 + TypeScript + Element Plus | `src/`（FOUND-010 创建） | 用户确认 + `docs/specification.md` | 已确认 |
| backend | 三个独立 FastAPI Agent API | `../agents/*` | 总体计划 | 已确认 |
| database | 前端不得直接访问数据库 | 不适用 | 总体架构 | 已确认 |
| ops | 由 agent-suite-ops 负责 | `../agent-suite-ops` | 总体计划 | 已确认 |

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
| 下一步 | 确认认证、路由、OpenAPI 类型与 SSE 交互 | `docs/plans/modules/agent-suite-web.md` | 已确认 |

## [manual] 外部服务

| 服务 | 用途/边界 | 来源 | 状态 |
|---|---|---|---|
| 数据库 | 不直连；通过 Agent API 获取数据 | 总体架构 | 已确认 |
| Redis |  |  | 待确认 |
| AI 服务 | 不直连 DeepSeek；只调用 Agent API | 总体架构 | 已确认 |
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
| 不接真实生产服务 | 未经用户确认不得连接真实生产 Agent、身份或外部服务 | 项目红线 | 已确认 |
| 不执行危险命令 | 不删除、覆盖、提交或推送用户内容，除非明确授权 | 项目红线 | 已确认 |
<!-- ai-facts:manual:end -->
