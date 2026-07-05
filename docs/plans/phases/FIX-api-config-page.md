# FIX-api-config-page

## Status

- Current stage: Stage 3 completed
- Owner: Codex
- Started: 2026-07-05

## Problem

API 配置页出现三个用户可见问题：

1. 页面内容区域偏右且上方 hero/card 过大，视觉位置不符合工作台设置页。
2. 表格为空时没有可点击编辑入口，用户无法补 API key。
3. 顶部 Toast 报 `Request failed with status code 500`。

## Evidence

- 用户截图：`/settings/api-config` 中 legal 表格显示“尚未配置”，无编辑按钮；右上角出现两个 500 Toast。
- 本地复现入口来自 `agent-suite-web/.env`：`VITE_API_BASE_URL=http://127.0.0.1:5666`。
- 直接请求结果：
  - `GET http://127.0.0.1:5666/api/legal/v1/me/api-config` -> 404
  - `GET http://127.0.0.1:5666/api/recruitment/v1/me/api-config` -> 500
  - `GET http://127.0.0.1:5666/api/data/v1/me/api-config` -> 500
- 旧 legal 日志显示运行进程未加载 `/me/api-config` 路由，且其他 DB 接口有 `DB session factory not initialized`。

## Impact

- 当前用户无法在 UI 中配置三个 Agent 的 API key。
- legal / recruitment / data 任一配置接口失败都会导致对应 tab 表格清空。
- 后端运行进程/网关是否加载最新代码需要单独处理；本阶段先保证页面可用并定位接口失败。

## Non-Goals

- 不接入真实 DeepSeek/OCR/MCP/飞书。
- 不重构全局布局或设计系统。
- 不修改用户全局配置。
- 不清空或重置数据库。

## Stages

### Stage 1: Restore Usable API Config Page

- 前端为三个 Agent 提供本地默认依赖项 fallback，接口失败时仍显示可编辑行。
- 将 404/500 转换为页面内错误状态，避免重复全局 Toast 淹没用户。
- 收紧设置页布局，让内容贴合当前工作台主内容区。
- 验证：
  - `pnpm.cmd typecheck` passed.
  - `pnpm.cmd lint` passed.
  - `pnpm.cmd test` passed: 13 files / 65 tests.
  - 新增 `admin-api-config-client.spec.ts` 覆盖默认可编辑行和加载错误静默配置。
  - HTTP 复现仍确认 5666 入口下 legal 404、recruitment/data 500；Stage 1 已在前端降级展示。
  - 浏览器验证：Chrome 访问 `http://127.0.0.1:5666/settings/api-config`，注入本地 dev 登录态后进入页面；默认依赖行可见，`编辑` 按钮计数 13，`Request failed with status code 500` Toast 计数 0，页面内错误提示计数 3。
  - UI polish 复验：将默认 `el-tabs` 改为自定义三段式 Agent 切换栏；Chrome 验证 `api-config-page__agent-tab` 计数 3，active tab 为 `法律咨询 Agent`，`编辑` 按钮计数 13，500 Toast 计数 0。

### Stage 2: Backend Runtime Alignment

- 确认 5666 网关后面的三个后端进程是否加载了最新代码。
- 对需要持久化保存的环境执行迁移/重启或补启动文档。
- 验证：`GET /me/api-config` 三个模块返回默认 items，`PUT` 可保存。

#### Stage 2 Result (2026-07-05)

- Root cause 1: recruitment returned 500 because SQLAlchemy could not infer the join for `UserModel.tasks` / `RecruitTaskModel.user`; `tasks` has both `user_id` and `reviewed_by` foreign keys to `users`.
- Fix: set explicit `foreign_keys` on `UserModel.tasks` and `RecruitTaskModel.user`; added `configure_mappers()` regression coverage.
- Root cause 2: after backend recovery, the web `recruitmentApi` request still got 401 because it did not send `x-user-public-id`.
- Fix: `recruitmentApi` now injects the current profile `public_id`; HTTP client unit test covers `x-user-public-id`.
- Runtime fix: `agent-suite-ops/scripts/stop-agent-runtime.ps1` used read-only PowerShell `$PID`; renamed the local variable so the project stop script works.
- Restart: stopped recruitment PID `46776`; started recruitment on `http://127.0.0.1:8102` with PID `46488`; live health passed.
- API smoke: legal / recruitment / data `GET http://127.0.0.1:5666/api/<agent>/v1/me/api-config` all returned 200.
- Save smoke: legal / recruitment / data `PUT .../me/api-config/deepseek` with fake key `sk-test-not-real` all returned 200; readback returns `api_key_hint=sk-t****real` and no `api_key` field.
- Browser verification: `http://127.0.0.1:5666/settings/api-config` shows three agent tabs, 10 editable rows, zero visible alerts, zero 500 toast; network requests for legal / recruitment / data config are all 200.
- Automated verification: recruitment pytest 32 passed; recruitment ruff passed; frontend unit tests 13 files / 66 tests passed; frontend typecheck passed.

### Stage 3: Agent Tab Interaction Fix

- New evidence: clicking the three custom Agent tabs updated button `active` / `aria-selected`, but the visible tabpanel stayed on the legal table. Runtime DOM showed `activeAgent` changed while panel display remained legal=`block`, recruitment/data=`none`.
- Root cause: the custom tab implementation kept three `v-show`-controlled Element Plus table panels in the DOM; the tab button state and panel display diverged.
- Fix: render a single current tabpanel keyed by `activeAgent`; use computed current-card/current-config/current-loading/current-error state for the active Agent.
- Regression test: added `agent-suite-web/tests/unit/api-config-admin-page.spec.ts`, asserting legal -> recruitment -> data clicks switch the visible table rows.
- Automated verification: `pnpm.cmd test -- tests\unit\api-config-admin-page.spec.ts tests\unit\admin-api-config-client.spec.ts` -> 14 files / 67 tests passed; `pnpm.cmd typecheck` -> passed.
- Browser verification: on `http://127.0.0.1:5666/settings/api-config`, legal shows 5 visible rows, recruitment shows 2, data shows 3; only 1 tabpanel exists; visible alert count is 0.

## Stop Conditions

- 需要停止或重启用户正在使用的进程但未获得确认。
- 需要破坏性数据库操作、清表、重置迁移或修改真实密钥。
- 后端日志包含真实密钥或隐私数据，需先脱敏再继续。

## Rollback

- 前端 fallback 和布局改动可通过回退 `agent-suite-web/src/views/admin/ApiConfigAdminPage.vue`、`agent-suite-web/src/api/admin-api-config.ts` 及相关类型文件撤销。
- 后端运行态调整如需执行，必须先确认具体命令和目标进程。
