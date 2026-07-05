# WEB-DATA Bridge 智能问数 Agent 前后端对接计划

## 状态

- 状态：执行中
- 日期：2026-07-05
- 模块：`agent-suite-web` 对接 `agents/data-query-agent` 公开 API/SSE 契约
- 任务等级：L3（前后端/API/SSE 对接）

## 依据

- 前端页面：`agent-suite-web/src/views/data/*`
- 后端契约：`agents/data-query-agent/docs/api-contract.md`
- 后端已实现 DTO：`agents/data-query-agent/src/data_query_agent/api/v1/schemas/*`
- 当前阶段：`docs/plans/current.md` 中 DATA-300 已完成本地计划范围，允许进入前端契约对接切片。

## 问题/现象

智能问数前端页面当前仍是占位页，尚未调用后端公开的线程、运行、SSE、查询历史和管理员 SQL 审计接口，用户无法从统一 Web 前端发起问数会话或查看后端返回的运行投影。

## 改动范围

只允许修改/新增以下范围：

- `agent-suite-web/src/api/data-query.ts`
- `agent-suite-web/src/types/data-query.ts`
- `agent-suite-web/src/lib/config.ts`
- `agent-suite-web/src/lib/http-client.ts`（仅为 data-query gateway subject header 做最小扩展）
- `agent-suite-web/src/views/data/DataSessionListPage.vue`
- `agent-suite-web/src/views/data/DataSessionPage.vue`
- `agent-suite-web/src/views/data/DataHistoryPage.vue`
- `agent-suite-web/src/views/data/admin/SqlAuditPage.vue`
- `agent-suite-web/tests/unit/data-query-client.spec.ts`
- `docs/plans/phases/WEB-DATA-bridge-data-query-agent.md`

如发现必须修改路由、App Shell、招聘 Agent、后端 Agent 或全局样式，停止并报告。

## 不做事项

- 不修改 `agents/recruitment-assistant-agent`。
- 不修改 `agents/data-query-agent` 后端代码。
- 不接真实 DeepSeek、真实 MySQL、真实飞书或生产服务。
- 普通用户页面不展示 generated SQL；仅管理员 SQL 审计页调用 `/admin/sql-audit`。
- 不猜测数据库字段，不读取后端私有模型作为前端展示来源；字段以公开 API DTO/schema 为准。
- 不提交 Git，除非用户后续明确要求。

## 接口映射

| 页面 | 前端能力 | 后端接口 |
|---|---|---|
| `/data/sessions` | 创建线程、查看线程列表、进入线程 | `POST /threads`, `GET /threads` |
| `/data/sessions/:id` | 查看线程、提交问题、查看 run 状态、SSE 投影、取消、重试 | `GET /threads/{thread_id}`, `POST /threads/{thread_id}/runs`, `GET /runs/{run_id}`, `GET /runs/{run_id}/stream`, `POST /runs/{run_id}/cancel`, `POST /runs/{run_id}/retry` |
| `/data/history` | 查询运行历史、打开历史详情 | `GET /query-history`, `GET /query-history/{query_id}` |
| `/data/admin/sql-audit` | 管理员查看 SQL 审计 | `GET /admin/sql-audit` |

## 分阶段步骤

### 阶段 1：API/SSE client 与类型

- 新增 data-query 契约类型。
- 新增集中 API client。
- 让 `dataApi` 请求带后端本地认证边界所需的 `X-User-Subject`，来源为已登录用户 public id，保留现有 Authorization。
- SSE 使用已有 `AgentStreamClient`，封装 stream URL 和 subject header 所需配置，不在页面直接拼接请求细节。

验证：`data-query-client.spec.ts` 覆盖路径、参数、body、编码、subject/header 配置。

### 阶段 2：智能问数页面接入

- 会话列表页：加载线程、创建线程、空/加载/错误状态。
- 会话详情页：加载线程、提交问题创建 run、展示当前问题和 run/SSE 状态、取消/重试。
- 历史页：加载 query-history、支持打开详情弹窗。
- SQL 审计页：管理员列表，展示 generated_sql，仅限该页面。

验证：typecheck/lint/format/test/build，必要时记录未验证原因。

## 验收标准

- 前端页面不再是占位页，能够调用 data-query-agent 公开接口。
- 所有请求集中在 `@api/data-query`，页面无散落 fetch/axios。
- 普通用户页面不显示 SQL。
- loading/error/empty/success 状态都有可见 UI。
- 最小单测覆盖 API client 契约映射。
- 本次 diff 不夹带招聘 Agent 或其他并行 AI 改动。

## 回滚/降级

- 回滚新增的 data-query API client、types、四个 data 页面和测试。
- 若后端不可用，前端显示错误/空状态，不启用 mock 伪装真实数据。

## 执行记录

- 2026-07-05：创建对接计划，确认前端智能问数页面仍为占位页，后端契约已公开线程、运行、SSE、历史和 SQL 审计接口。

- 2026-07-05????? 1-2??? data-query ??????? API client??? HTTP/SSE client ?? `X-User-Subject`????????????????????????SSE??????? SQL ???????????????? SQL???? SQL ??????? generated_sql????
  - `pnpm.cmd typecheck`????
  - `pnpm.cmd lint`????
  - `pnpm.cmd test`?11 files / 58 tests passed?
  - `pnpm.cmd build`???????? Rollup/Vite warning?Element Plus chunk > 500 kB?echarts empty chunk?@vueuse/core PURE ????
  - `pnpm.cmd format:check`???????????????????? `src/views/legal/*` ???????????? `prettier --check <changed files>` ????
