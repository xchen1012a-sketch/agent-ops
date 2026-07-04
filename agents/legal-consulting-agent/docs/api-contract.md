# 法律咨询 API 草案

基础运行接口遵循运维仓 `docs/contracts/api-conventions.md`。

## 领域资源

```text
POST   /v1/auth/register
POST   /v1/auth/login
PUT    /v1/auth/password
GET    /v1/legal-categories
POST   /v1/threads
GET    /v1/threads
DELETE /v1/threads/{thread_id}
POST   /v1/threads/{thread_id}/runs
GET    /v1/consultations
GET    /v1/consultations/{consultation_id}
POST   /v1/consultations/export
```

## 运行输入草案

- `message`：用户问题。
- `category_id`：法律分类。
- `attachments`：可选材料引用，不直接传服务器文件路径。
- `idempotency_key`：客户端重试去重键。

## 运行输出草案

- 回答正文。
- 风险/免责声明。
- 来源列表。
- 运行状态和 `run_id`。
- 可重试标记。

字段名和 Schema 在 `LEGAL-110` 固化并生成 OpenAPI，当前仅定义资源边界。

