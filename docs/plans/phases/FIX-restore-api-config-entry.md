# FIX Restore API Config Entry

## Status

Completed on 2026-07-06.

## Problem

API 配置页面的路由和页面还存在，但侧边栏入口在 MVP 精简时被移除，用户无法从主导航直达配置页。

## Evidence

- `agent-suite-web/src/router/index.ts` 仍有 `/settings/api-config` 和 `admin-api-config` 路由。
- `agent-suite-web/src/views/admin/ApiConfigAdminPage.vue` 仍存在。
- `agent-suite-web/src/app/AppHeader.vue` 顶部用户菜单仍有 API 配置项，但入口不明显。
- `agent-suite-web/src/app/AppSidebar.vue` 当前只显示 Agent 和最近对话，没有 API 配置入口。

## Scope

- 恢复侧边栏 API 配置入口。
- 不恢复侧边栏底部收缩按钮。
- 不修改 API 配置页面业务逻辑和后端接口。
- 不改动真实 API key、外部服务配置或全局配置。

## Steps

1. 在侧边栏增加 API 配置导航按钮，非折叠状态显示文字，折叠状态可通过 title 识别。
2. 让 `/settings/api-config` 路由时该入口高亮。
3. 运行前端 typecheck，并用本地页面/API 做 smoke。

## Verification

- `npm.cmd run typecheck`
- `GET http://127.0.0.1:7777/settings/api-config` 返回页面。
- `npm.cmd run lint`
- 登录后调用三个配置列表接口：
  - `/api/legal/v1/me/api-config` -> 200
  - `/api/recruitment/v1/me/api-config` -> 200
  - `/api/data/v1/me/api-config` -> 200
- Playwright visual smoke 未执行成功：本机缺少 Playwright Chromium 二进制。接口和类型/静态检查已覆盖本次恢复入口的最小验证。

## Rollback

移除本次在 `AppSidebar.vue` 中新增的 API 配置入口和样式。
