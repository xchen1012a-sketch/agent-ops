# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: 491b3e0302dc6b6a
- last refresh: 2026-07-08 17:45:25 +0800
- refresh command: scripts/refresh-project-facts.sh

## [auto] Tech stack

- No package.json parser available.

## [auto] Scripts

- No package.json scripts detected.

## [auto] Directory structure (top 2 levels)

```text
agent-ops/
|-- .DS_Store
|-- .gitattributes
|-- .gitignore
|-- .pip-cache
|   |-- .pip-cache/http-v2
|   |-- .pip-cache/selfcheck
|-- .venv
|   |-- .venv/.gitignore
|   |-- .venv/bin
|   |-- .venv/include
|   |-- .venv/lib
|   |-- .venv/pyvenv.cfg
|   |-- .venv/share
|-- AGENTS.md
|-- CLAUDE.md
|-- README.md
|-- agent-suite-ops
|   |-- agent-suite-ops/.env.example
|   |-- agent-suite-ops/.gitignore
|   |-- agent-suite-ops/AGENTS.md
|   |-- agent-suite-ops/CLAUDE.md
|   |-- agent-suite-ops/README.md
|   |-- agent-suite-ops/docker-compose.local.yml
|   |-- agent-suite-ops/docker-compose.yml
|   |-- agent-suite-ops/docs
|   |-- agent-suite-ops/nginx
|   |-- agent-suite-ops/scripts
|-- agent-suite-web
|   |-- agent-suite-web/.dockerignore
|   |-- agent-suite-web/.editorconfig
|   |-- agent-suite-web/.env.example
|   |-- agent-suite-web/.eslintrc-auto-import.json
|   |-- agent-suite-web/.gitignore
|   |-- agent-suite-web/.npmrc
|   |-- agent-suite-web/.pnpm-store
|   |-- agent-suite-web/AGENTS.md
|   |-- agent-suite-web/CLAUDE.md
|   |-- agent-suite-web/Dockerfile
|   |-- agent-suite-web/README.md
|   |-- agent-suite-web/auto-imports.d.ts
|   |-- agent-suite-web/components.d.ts
|   |-- agent-suite-web/dev-auth-plugin.ts
|   |-- agent-suite-web/docs
|   |-- agent-suite-web/eslint.config.mjs
|   |-- agent-suite-web/index.html
|   |-- agent-suite-web/nginx
|   |-- agent-suite-web/package.json
|   |-- agent-suite-web/playwright.config.ts
|   |-- agent-suite-web/pnpm-lock.yaml
|   |-- agent-suite-web/pnpm-workspace.yaml
|   |-- agent-suite-web/public
|   |-- agent-suite-web/src
|   |-- agent-suite-web/tests
|   |-- agent-suite-web/tsconfig.json
|   |-- agent-suite-web/tsconfig.node.json
|   |-- agent-suite-web/vite.config.ts
|   |-- agent-suite-web/vitest.config.ts
|-- agents
|   |-- agents/.DS_Store
|   |-- agents/auth-service
|   |-- agents/data-query-agent
|   |-- agents/legal-consulting-agent
|   |-- agents/recruitment-assistant-agent
|-- docs
|   |-- docs/contracts
|   |-- docs/homework
|   |-- docs/plans
```

## [auto] Environment keys

- No .env*.example keys detected.

## [auto] Git status

- Current branch: develop
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
| 产品定位 | 统一前端、三个独立 Agent API、一个运维协调模块，单仓管理 | 总体计划 + ADR-0006 | 已确认 |
| 业务域 | 法律咨询、智能招聘、智能问数 | 课件 + 用户确认 | 已确认 |
| Git 形态 | 根目录单仓；agent-suite-web、agent-suite-ops、agents/* 为工程模块 | 用户于 2026-07-04 确认 + ADR-0006 | 已确认 |
| 远端 | https://github.com/xchen1012a-sketch/agent-ops.git，分支 main / develop | ARCH-003 验收 | 已确认 |

## [manual] 模块词表

| 模块 | 说明 | 命名前缀/目录 | 来源 | 状态 |
|---|---|---|---|---|
| frontend | 统一 Vue 3 前端、Element Plus、Vite、TypeScript | `agent-suite-web/`，端口 5173 | ADR-0006、ADR-0011 | 已确认 |
| legal | 法律咨询 Agent：FastAPI + LangGraph + RAG | `agents/legal-consulting-agent/`，端口 8101 | 模块计划 + ADR-0011 | 已确认 |
| recruitment | 智能招聘 Agent：FastAPI + LangGraph + 公平性规则 | `agents/recruitment-assistant-agent/`，端口 8102 | 模块计划 + ADR-0011 | 已确认 |
| data-query | 智能问数 Agent：FastAPI + LangGraph + NL2SQL + MCP | `agents/data-query-agent/`，端口 8103 | 模块计划 + ADR-0011 | 已确认 |
| ops | 运维协调：Docker Compose、Nginx、Runbook | `agent-suite-ops/`，端口 80/443 | 模块计划 + ADR-0011 | 已确认 |
| database | MySQL 8.0.36；4 schema 独立账号 | `legal_agent_db` / `recruitment_agent_db` / `data_query_agent_db` / `shop_db`(只读) | ADR-0011 | 已确认 |

## [manual] 阶段前缀

| 前缀 | 含义 | 来源 | 状态 |
|---|---|---|---|
| ARCH | 架构基线与单仓迁移 | `docs/plans/phases/ARCH-00*` | 已确认 |
| DESIGN | 跨模块设计对齐 | `docs/plans/phases/DESIGN-00*` | 已确认 |
| FOUND | 公共工程基础 | `docs/plans/phases/FOUND-0*` | 已确认 |
| LEGAL | 法律 Agent 子阶段 | `docs/plans/modules/legal-consulting-agent.md` | 已确认 |
| RECRUIT | 招聘 Agent 子阶段 | `docs/plans/modules/recruitment-assistant-agent.md` | 已确认 |
| DATA | 智能问数 Agent 子阶段 | `docs/plans/modules/data-query-agent.md` | 已确认 |
| WEB | 前端子阶段 | `docs/plans/modules/agent-suite-web.md` | 已确认 |
| OPS | 运维子阶段 | `docs/plans/modules/agent-suite-ops.md` | 已确认 |
| FEISHU | 飞书接入 | `docs/plans/modules/data-query-agent.md` §FEISHU-500 | 已确认 |
| QA | 质量验收 | `docs/plans/project-plan.md` | 已确认 |
| REPORT | 报告与演示 | `docs/plans/project-plan.md` | 已确认 |

## [manual] 当前阶段

| 字段 | 值 | 来源 | 状态 |
|---|---|---|---|
| 当前阶段 | LEGAL-100 法律咨询 Agent 业务实现 | `docs/plans/current.md` | 已确认 |
| 状态 | `LEGAL-130 身份与数据层` 第一批 6 张表已实现并通过本地验证 | `docs/plans/current.md` + `docs/plans/phases/LEGAL-100-legal-consulting-agent.md` | 已确认 |
| 已落地 | ADR-0007 统一认证、ADR-0008 法律 RAG、ADR-0009 招聘公平性、ADR-0010 SQL 安全、ADR-0011 部署参数、ADR-0012 法律混合检索修订 | `agent-suite-ops/docs/adr/` + `docs/plans/current.md` | 已确认 |

## [manual] 外部服务

| 服务 | 用途/边界 | 来源 | 状态 |
|---|---|---|---|
| 数据库 | MySQL 8.0.36 LTS；4 schema 独立账号；shop_db 严格只读 | ADR-0011 | 已确认 |
| Redis | 7.4-alpine；限流 + SSE 心跳 + 短期缓存（Embedding/SQL 摘要）；不持久化业务数据 | ADR-0011 | 已确认 |
| AI 服务 | DeepSeek 官方 API / `deepseek-chat`；直连；超时 60s 重试 3 次 | 用户确认 + ADR-0011 | 已确认 |
| Embedding | BGE-M3 自托管（sentence-transformers，CPU 推理） | ADR-0008 | 已确认 |
| 向量库 | 法律 Agent 使用 Qdrant 1.12+；BGE-M3 dense/sparse + BGE reranker 混合检索；ADR-0012 修订 ADR-0008 检索策略 | ADR-0012 | 已确认 |
| MCP server | 沿用课件 MCP server 作为智能问数查询主链路 | ADR-0010 | 已确认 |
| 反向代理 | Nginx 1.27-alpine；统一入口 + SSE 长连接 | ADR-0011 | 已确认 |
| 飞书 | 测试租户与凭据推迟到 FEISHU-500 阶段对齐 | ADR-0011 + 数据模块计划 | 已确认 |
| 对象存储 | 首期不引入；招聘文件解析后立即删除，不持久化 | ADR-0009 | 已确认 |

## [manual] 生成与禁改路径

| 类型 | 路径 | 规则 | 来源 | 状态 |
|---|---|---|---|---|
| 自动生成目录 | `*/migrations/versions/` | Alembic autogenerate；不手改；记录命令 | ADR-0011 + 数据库标准 | 已确认 |
| 自动生成目录 | `agent-suite-web/src/api/types/` | openapi-typescript 从契约生成；不手改 | 前端计划 WEB-410 | 已确认 |
| 禁止手改目录 | `.ai-spec/` | 项目规则；只读 | 项目规则 | 已确认 |
| 禁止手改目录 | 已验收阶段文件 `docs/plans/phases/*.md` | 验收证据冻结；如要修订需新建 ADR | 项目规则 | 已确认 |
| 禁止手改目录 | `agent-suite-ops/docs/adr/` | ADR 已确认不可改；新决策新建编号 | ADR 约定 | 已确认 |
| 只能命令生成 | Alembic 迁移文件 | `alembic revision --autogenerate -m "..."` | 数据库标准 | 已确认 |
| 只能命令生成 | OpenAPI TypeScript 类型 | `pnpm openapi-typescript ...` | 前端计划 | 已确认 |

## [manual] 安全边界

| 边界 | 规则 | 来源 | 状态 |
|---|---|---|---|
| 不接真实生产服务 | 未经用户确认不接生产数据库、飞书、真实用户或候选人数据 | 项目红线 | 已确认 |
| 不执行危险命令 | 不删除/覆盖用户内容，不自动提交或推送，不执行 LLM 生成的命令/SQL | 项目红线 | 已确认 |
| 不硬编码 | 密钥、地址、模型名、Prompt、SQL 白名单、评分权重、敏感属性清单等必须归属到类型化 Settings 或版本化规则真源 | ADR-0004 + ADR-0007~0011 | 已确认 |
| SQL 安全 | 仅 SELECT；sqlglot AST + 表/列/函数白名单；shop_db 独立只读账号；LLM 输出不得直接执行 | ADR-0010 | 已确认 |
| 招聘公平性 | 敏感属性解析阶段剔除；权重在版本化规则真源；所有匹配 admin 签字后才能出报告 | ADR-0009 | 已确认 |
| 法律合规 | 不联网检索；引用附来源+章节+原文片段；高风险转人工；每回答附免责声明 | ADR-0008 | 已确认 |
| 认证安全 | JWT 密钥环境变量；refresh HTTP-only Cookie；BCrypt cost=12；密码修改失效所有 token | ADR-0007 | 已确认 |
| 日志脱敏 | 不记录密钥、Token、完整 Prompt、简历原文、法律咨询原文、SQL 完整结果 | ADR-0011 | 已确认 |
<!-- ai-facts:manual:end -->
