# 可观测性契约

## 日志字段

统一字段：`timestamp`、`level`、`service`、`environment`、`request_id`、`thread_id`、`run_id`、`node_name`、`status`、`duration_ms`、`error_code`。

禁止记录：API Key、Authorization、Cookie、完整 Prompt、完整简历、完整法律咨询、MySQL 明细结果、个人联系方式。

## 指标

- `http_requests_total`
- `http_request_duration_seconds`
- `agent_runs_total`
- `agent_run_duration_seconds`
- `agent_node_failures_total`
- `llm_requests_total`
- `llm_request_duration_seconds`
- `llm_tokens_total`
- `db_query_duration_seconds`

指标标签仅使用服务、路由模板、状态码、Agent/节点名和错误类别，禁止使用用户输入或公开 ID 作为标签。

## Trace

一次用户请求使用同一 `request_id`；一次 Agent 执行使用 `run_id`；多轮会话使用 `thread_id`。节点、LLM、工具和数据库 span 必须关联同一 trace。

