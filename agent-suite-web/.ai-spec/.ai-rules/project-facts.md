# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: 6762ea778d81c04b
- last refresh: 2026-07-05 00:52:36 +0800
- refresh command: scripts/refresh-project-facts.sh

## [auto] Tech stack

- vue ^3.5.12
- vite ^5.4.8
- typescript ~5.6.2
- vitest ^2.1.2
- @playwright/test ^1.48.0
- eslint ^9.12.0
- prettier ^3.3.3

## [auto] Scripts

- build: vue-tsc --noEmit && vite build
- dev: vite
- e2e: playwright test
- e2e:install: playwright install --with-deps
- format: prettier --write "src/**/*.{ts,vue,css,scss,json,md}"
- format:check: prettier --check "src/**/*.{ts,vue,css,scss,json,md}"
- lint: eslint . --max-warnings=0
- lint:fix: eslint . --fix
- preview: vite preview --port 5173
- test: vitest run
- test:coverage: vitest run --coverage
- test:watch: vitest
- typecheck: vue-tsc --noEmit

## [auto] Directory structure (top 2 levels)

```text
agent-suite-web/
|-- .dockerignore
|-- .editorconfig
|-- .env.example
|-- .eslintrc-auto-import.json
|-- .gitignore
|-- .npmrc
|-- AGENTS.md
|-- CLAUDE.md
|-- Dockerfile
|-- README.md
|-- auto-imports.d.ts
|-- components.d.ts
|-- docs
|   |-- docs/api-integration.md
|   |-- docs/architecture.md
|   |-- docs/detailed-design.md
|   |-- docs/specification.md
|-- eslint.config.mjs
|-- index.html
|-- nginx
|   |-- nginx/default.conf
|-- package.json
|-- playwright.config.ts
|-- pnpm-lock.yaml
|-- pnpm-workspace.yaml
|-- public
|   |-- public/favicon.svg
|-- src
|   |-- src/App.vue
|   |-- src/api
|   |-- src/app
|   |-- src/components
|   |-- src/env.d.ts
|   |-- src/lib
|   |-- src/main.ts
|   |-- src/router
|   |-- src/stores
|   |-- src/styles
|   |-- src/types
|   |-- src/views
|   |-- src/vue-shims.d.ts
|-- tests
|   |-- tests/setup.ts
|   |-- tests/unit
|-- tsconfig.json
|-- tsconfig.node.json
|-- vite.config.ts
|-- vitest.config.ts
```

## [auto] Environment keys

- VITE_API_AUTH_PREFIX
- VITE_API_BASE_URL
- VITE_API_DATA_PREFIX
- VITE_API_LEGAL_PREFIX
- VITE_API_RECRUITMENT_PREFIX
- VITE_DEFAULT_THEME
- VITE_SESS_TIMEOUT_MINUTES

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
| 当前阶段 | FOUND-010 企业级工程基础 | 父目录 `docs/plans/current.md` | 已确认 |
| 下一步 | 等待用户授权进入 WEB-400；前端后续基于 OpenAPI Mock 与业务切片联调 | 父目录 `docs/plans/current.md` + `docs/plans/modules/agent-suite-web.md` | 已确认 |

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
