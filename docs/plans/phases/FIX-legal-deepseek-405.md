# FIX Legal DeepSeek HTTP 405

## Status

Completed on 2026-07-06.

## Problem

法律助手会话页显示 `deepseek stream failed: HTTP 405`。用户已经在 API 配置页配置了 DeepSeek，但上游返回 Method Not Allowed。

## Evidence

- 法律助手当前用户 `deepseek` 配置为 enabled。
- `api_key_hint` 存在，说明 key 已保存。
- 当前 `base_url` 为 `https://platform.deepseek.com/v1`。
- 法律助手后端适配器会把 `base_url.rstrip("/") + "/chat/completions"` 作为真实请求地址。
- DeepSeek 官方 API 文档给出的 OpenAI 兼容 `base_url` 是 `https://api.deepseek.com`，示例请求是 `https://api.deepseek.com/chat/completions`。

## Root Cause

配置的是 DeepSeek 控制台/平台域名，不是 API 域名。后端已经读取并使用配置，所以报错不是“没配置”，而是“配置地址不对”。

## Scope

- 修正当前账号法律助手 DeepSeek `base_url`。
- 不读取、不打印、不替换已保存的真实 API key。
- 不改动外部服务密钥和全局配置。
- 如有必要，补充 UI/后端防误填提示或归一化。

## Verification

- 配置列表显示 legal deepseek `base_url` 为 `https://api.deepseek.com`。
- 重新触发法律助手流式问答，不再出现 405。
- 2026-07-06 复验：
  - `PUT /api/legal/v1/me/api-config/deepseek` 返回 200。
  - 返回配置：enabled=true，base_url=`https://api.deepseek.com`，model=`deepseek-chat`，api_key_hint 保持原有脱敏值。
  - `POST /api/legal/v1/sessions/{id}/questions/events` 返回 HTTP 200。
  - SSE 样本包含 `run.started` 和 `message.delta`，未出现 `HTTP 405` 或 `run.failed`。

## Rollback

通过 API 配置页把法律助手 DeepSeek Base URL 改回旧值；不影响已保存 key。
