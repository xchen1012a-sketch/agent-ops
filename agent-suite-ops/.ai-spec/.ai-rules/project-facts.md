# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: 4a1a6d1b4d183307
- last refresh: 2026-07-04 21:11:16 +08:00
- refresh command: scripts/refresh-project-facts.ps1

## [auto] Tech stack

- No common framework or tool detected from package.json.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
agent-suite-ops/
|-- docs/
|   |-- adr/
|   |-- architecture/
|   |-- contracts/
|   |-- runbooks/
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
| 项目名称 | agent-suite-ops | 用户确认 + 总体计划 | 已确认 |
| 产品定位 | 五仓部署、网关、环境和可观测协调仓库 | `README.md` | 已确认 |
| 业务域 | Docker 编排、反向代理、环境模板、运维与排障 | `README.md` | 已确认 |
| 仓库/子仓命名 | agent-suite-ops | 用户确认 | 已确认 |

## [manual] 模块词表

| 模块 | 说明 | 命名前缀/目录 | 来源 | 状态 |
|---|---|---|---|---|
| frontend |  |  |  | 待确认 |
| backend |  |  |  | 待确认 |
| database |  |  |  | 待确认 |
| ops | 跨仓 Docker Compose、网关、健康检查、可观测 | 仓库根与 `docs/` | `README.md` + 总体计划 | 已确认 |

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
| 下一步 | 确认端口、数据库权限、Secret 与部署拓扑 | `docs/plans/modules/agent-suite-ops.md` | 已确认 |

## [manual] 外部服务

| 服务 | 用途/边界 | 来源 | 状态 |
|---|---|---|---|
| 数据库 | MySQL 8 开发拓扑；四个权限域待 DESIGN-002 固化 | 总体架构 + 模块计划 | 部分确认 |
| Redis |  |  | 待确认 |
| AI 服务 | DeepSeek 官方 API，由三个 Agent 独立调用 | ADR-0003 | 已确认 |
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
| 不接真实生产服务 | 未经用户确认不部署或连接真实生产环境 | 项目红线 | 已确认 |
| 不执行危险命令 | 不删除卷、数据或远程资源，不自动 push | 项目红线 | 已确认 |
<!-- ai-facts:manual:end -->
