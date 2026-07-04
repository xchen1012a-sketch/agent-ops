# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: 9d84cb626f49e164
- last refresh: 2026-07-04 21:37:10 +08:00
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

- No common framework or tool detected from package.json.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
agent/
|-- agents/
|   |-- data-query-agent/
|   |-- legal-consulting-agent/
|   |-- recruitment-assistant-agent/
|-- agent-suite-ops/
|   |-- docs/
|   |-- .gitignore
|   |-- AGENTS.md
|   |-- CLAUDE.md
|   |-- README.md
|-- agent-suite-web/
|   |-- docs/
|   |-- .gitignore
|   |-- AGENTS.md
|   |-- CLAUDE.md
|   |-- README.md
|-- AI编程_智能问数实训(课件)/
|   |-- 01_课程导论与行业概览/
|   |-- 02_环境准备/
|   |-- 03_AI法律咨询系统实战/
|   |-- 04_Docker容器技术实战/
|   |-- 05_Dify工作流智能体开发/
|   |-- 06_智能问数/
|   |-- feishu-to-dify/
|   |-- shop_db_export.sql
|-- docs/
|   |-- homework/
|   |-- plans/
|-- .gitignore
|-- AGENTS.md
|-- CLAUDE.md
|-- README.md
```

## [auto] Environment keys

- No .env*.example keys detected.

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
| 项目名称 | enterprise-agent-suite（企业级多智能体应用平台） | 用户确认 + `docs/plans/project-plan.md` | 已确认 |
| 产品定位 | 统一前端、三个独立Agent API、一个运维协调仓库 | 总体计划 | 已确认 |
| 业务域 | 法律咨询、智能招聘、智能问数 | 课件 + 用户确认 | 已确认 |
| Git 形态 | 根目录单仓；agent-suite-web、agent-suite-ops、agents/* 为工程模块 | 用户于 2026-07-04 确认 | 已确认 |

## [manual] 模块词表

| 模块 | 说明 | 命名前缀/目录 | 来源 | 状态 |
|---|---|---|---|---|
| frontend |  |  |  | 待确认 |
| backend |  |  |  | 待确认 |
| database |  |  |  | 待确认 |
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
| 当前阶段 | DESIGN-002 模块详细设计对齐 | `docs/plans/current.md` | 已确认 |
| 下一步 | 逐模块清零详细设计未决问题，用户确认后进入FOUND-010 | `docs/plans/current.md` | 已确认 |

## [manual] 外部服务

| 服务 | 用途/边界 | 来源 | 状态 |
|---|---|---|---|
| 数据库 | MySQL 8；按模块独立权限域 | 总体计划 | 已确认 |
| Redis |  |  | 待确认 |
| AI 服务 | DeepSeek官方API/deepseek-chat | 用户确认 | 已确认 |
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
| 不接真实生产服务 | 未经用户确认不接生产数据库、飞书、真实用户或候选人数据 | 项目红线 | 已确认 |
| 不执行危险命令 | 不删除/覆盖用户内容，不自动提交或推送，不执行LLM生成命令/SQL | 项目红线 | 已确认 |
<!-- ai-facts:manual:end -->
