# 智能问数 API 草案

基础运行接口遵循运维仓 `docs/contracts/api-conventions.md`。

## 领域资源

```text
POST   /v1/threads
GET    /v1/threads
POST   /v1/threads/{thread_id}/runs
GET    /v1/runs/{run_id}
GET    /v1/runs/{run_id}/stream
POST   /v1/runs/{run_id}/cancel
POST   /v1/runs/{run_id}/retry
GET    /v1/query-history
GET    /v1/query-history/{query_id}
POST   /v1/evaluations
GET    /v1/evaluations/{evaluation_id}
POST   /v1/integrations/feishu/events
```

长连接飞书模式不一定使用 HTTP events 入口，最终接口由 `FEISHU-500` 详细设计确认。

## 运行输入草案

- `question`
- `thread_id`
- `timezone`
- `locale`
- `channel`：`web` 或 `feishu`
- `idempotency_key`

## 运行输出草案

- `answer`
- `data.columns` / `data.rows` / `data.truncated`
- `chart.type` / `chart.dataset` / `chart.encoding`
- `query_summary`
- `run_id` / `status` / `warnings`

默认不向普通用户暴露原始 SQL；管理员调试权限和脱敏规则在 `DATA-310` 确认。

## DATA-360 Thread API slice

Authentication boundary for local API tests uses gateway-provided `X-User-Subject` as the upstream subject placeholder. Production auth integration remains outside this slice.

Thread endpoints return public DTOs only; internal `user_id` is not exposed.

```text
POST /v1/threads
GET  /v1/threads?limit=20&offset=0
GET  /v1/threads/{thread_id}
```

Success envelope:

```json
{
  "data": {},
  "error": null
}
```

Thread DTO fields:

- `thread_id`
- `title`
- `status`
- `created_at`
- `updated_at`

## DATA-360 Run creation API slice

`POST /v1/threads/{thread_id}/runs` creates a user question message and a pending run only. It does not execute workflow and does not return generated SQL.

Request fields:

- `question` required, 1..2000 chars
- `timezone` optional
- `locale` optional
- `channel` optional: `web` or `feishu`, default `web`
- `idempotency_key` optional placeholder; dedup semantics are not implemented in this slice

Response DTO fields:

- `run_id`
- `thread_id`
- `status`
- `question`
- `created_at`
- `started_at`
- `finished_at`

## DATA-360 Run detail API slice

`GET /v1/runs/{run_id}` returns an ownership-scoped run status projection. It does not trigger workflow execution and does not expose generated SQL.

Response DTO fields:

- `run_id`
- `status`
- `error_code`
- `error_message`
- `created_at`
- `started_at`
- `finished_at`

## DATA-360 SSE event contract slice

`GET /v1/runs/{run_id}/stream` returns an ownership-scoped SSE projection for current run and node states. This slice emits contract events only; it does not implement token-level streaming or subscribe to a real background queue.

Event names:

- `run.started`
- `node.started`
- `node.completed`
- `node.failed`
- `run.completed`
- `run.failed`

