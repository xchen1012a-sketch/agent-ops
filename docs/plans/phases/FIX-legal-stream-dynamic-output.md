# FIX Legal Stream Dynamic Output

## Status

Completed on 2026-07-06.

## Problem

法律助手页面没有体现真实动态思考/回答过程，历史助手消息还显示类似加载中的红色放射图标。用户配置 DeepSeek 后，页面仍主要展示本地固定回答。

## Evidence

- `legal_questions.py` 的 `_thinking_then_answer()` 只转发 `chunk.kind == "thinking"`，把真实模型的 `answer` chunks 丢弃。
- 转发完 thinking 后，后端再把本地 deterministic answer 切片输出。
- `LegalSessionPage.vue` 对所有历史 assistant 消息使用红色放射头像，视觉上像一直在加载。
- 前端 `useAgentStream` 本身能处理 `message.thinking.delta` 与 `message.delta`，问题主要在后端桥接和头像状态。

## Root Cause

后端法律流式接口最初只把真实模型当“thinking provider”，没有把真实 answer 作为最终回答来源；前端历史消息头像没有区分“历史消息”和“正在生成”。

## Scope

- 法律 SSE：安全地输出进度型 thinking，再转发真实模型 thinking/answer。
- 如果真实模型提供 answer chunks，用真实 answer 写回助手消息；如果没有真实 answer，回退本地 deterministic answer。
- Fake/local adapter 保持使用本地 deterministic answer，避免 mock 占位内容污染消息。
- 前端历史助手头像改为静态标识，只有 pending 消息显示生成动画。

## Verification

- legal targeted pytest。
- frontend typecheck/lint。
- 本地 legal SSE smoke：应包含 thinking delta、message delta、message.completed，且不是 HTTP 405。
- 2026-07-06 复验结果：
  - `pytest tests/unit/test_legal_questions_api.py tests/unit/test_deepseek_stream_adapter.py tests/unit/test_sse_forwarder.py` -> `10 passed`。
  - `ruff check` on changed legal backend/test files -> passed。
  - targeted `mypy` on changed legal backend/test files -> passed。
  - `agent-suite-web` `npm.cmd run lint` -> passed。
  - `agent-suite-web` `npm.cmd run typecheck` -> passed。
  - legal 后端已重启，live health passed。
  - `POST /api/legal/v1/sessions/{id}/questions/events` -> HTTP 200，包含 `message.thinking.delta`、`message.thinking.completed`、`message.delta`、`message.completed`，未出现 `HTTP 405` 或 `run.failed`。
  - 最新 assistant 消息已写回为 `prompt_version=deepseek:stream-v1`，内容为真实流式回答，不再是 deterministic fallback。

## Rollback

恢复 `legal_questions.py` 的旧 `_thinking_then_answer()` 逻辑，移除消息内容更新方法，恢复 `LegalSessionPage.vue` 助手头像样式。
