# 跨仓 API 契约约定

## 1. 基础约定

- 路径版本：`/v1`。
- 数据格式：UTF-8 JSON；流式接口使用 SSE。
- 时间：ISO 8601，统一 UTC 存储，展示层转换时区。
- 标识符：不暴露数据库自增主键，公开 ID 使用不可预测字符串。
- OpenAPI：每个 Agent 仓库维护自己的真源契约。

## 2. 建议公共资源语义

```text
POST   /v1/threads
GET    /v1/threads/{thread_id}
GET    /v1/threads/{thread_id}/messages
POST   /v1/threads/{thread_id}/runs
GET    /v1/runs/{run_id}
GET    /v1/runs/{run_id}/stream
POST   /v1/runs/{run_id}/cancel
POST   /v1/runs/{run_id}/retry
GET    /health/live
GET    /health/ready
```

各服务可以添加领域资源，但不得改变上述公共语义。

## 3. 标准响应

非流式成功响应至少包含 `request_id`、资源主体和服务版本。异步运行响应包含 `run_id`、`thread_id`、`status`。

错误响应：

```json
{
  "request_id": "opaque-id",
  "error": {
    "code": "AGENT_DEPENDENCY_TIMEOUT",
    "message": "外部服务响应超时",
    "retryable": true,
    "details": {}
  }
}
```

`details` 不得包含栈、SQL、Prompt、Token 或隐私数据。

## 4. SSE 事件

统一事件类型：`run.started`、`node.started`、`message.delta`、`tool.started`、`tool.completed`、`run.completed`、`run.failed`、`run.canceled`、`heartbeat`。

事件至少包含 `event_id`、`request_id`、`run_id`、`sequence`、`timestamp` 和脱敏 payload。客户端必须按 `sequence` 去重并允许断线恢复策略。

## 5. 兼容性

- 增加可选字段视为向后兼容。
- 删除字段、改变类型、改变错误码语义必须提升 API 主版本。
- 前端不得依赖未进入 OpenAPI 的响应字段。

