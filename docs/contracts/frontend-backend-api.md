# 前端对接后端接口契约（agent-suite-web → 三 Agent 后端）

> 本文档面向后端开发，用于对齐 `agent-suite-web` 前端已实现/已约定的 HTTP 与 SSE 接口。
>
> **字段来源（全部取自前端真实代码，未猜测）**：
> - `agent-suite-web/src/lib/config.ts`（网关前缀、HTTP client 装配）
> - `agent-suite-web/src/lib/http-client.ts`（请求头、错误 envelope、错误码映射）
> - `agent-suite-web/src/lib/sse-client.ts`（SSE 帧协议、鉴权头、重连）
> - `agent-suite-web/src/api/{auth,legal,data-query,recruitment}.ts`（端点、方法、路径、请求/响应类型）
> - `agent-suite-web/src/types/{auth,api,legal,data-query,recruitment,sse,agent,health}.ts`（DTO 字段与类型）
> - `agent-suite-web/src/views/recruitment/*`（任务列表/新建/详情+SSE/报告/admin 复核，已全部接线）
> - 招聘域后端 schema（字段权威来源）：`agents/recruitment-assistant-agent/src/recruitment_assistant_agent/api/v1/schemas/recruitment_*.py`、`domain/value_objects/recruit_enums.py`

---

## 1. 通用约定

### 1.1 网关前缀

前端通过环境变量配置各域前缀（`config.ts`），默认值：

| 域 | 环境变量 | 默认前缀 |
|---|---|---|
| 认证 | `VITE_API_AUTH_PREFIX` | `/api/auth` |
| 法律 | `VITE_API_LEGAL_PREFIX` | `/api/legal/v1` |
| 招聘 | `VITE_API_RECRUITMENT_PREFIX` | `/api/recruitment/v1` |
| 数据问数 | `VITE_API_DATA_PREFIX` | `/api/data/v1` |

- 基础地址：`VITE_API_BASE_URL`（默认空字符串，即同源；生产由 Nginx 网关路由到各后端）。
- 最终 URL = `apiBaseUrl + <域前缀> + <端点相对路径>`。
- 注意：认证域前缀 **不带 `/v1`**；法律/招聘/数据域前缀 **已含 `/v1`**，故本文档端点相对路径不再重复 `/v1`。

### 1.2 请求头（所有非认证域请求，见 `http-client.ts`）

| Header | 取值 | 说明 |
|---|---|---|
| `Content-Type` | `application/json` | 固定 |
| `Accept` | `application/json` | 固定 |
| `Authorization` | `Bearer <access_token>` | 有 token 时注入 |
| `X-Request-ID` | 每请求生成的 UUID | 幂等/链路追踪 |
| `x-user-public-id` | 用户 `public_id` | **仅法律域**注入（`getUserPublicId`） |
| `X-User-Subject` | 用户 `public_id` | **仅数据域**注入（`getUserSubject`） |

- 所有 client 均 `withCredentials: true`（携带 cookie，用于 refresh token）。
- 默认超时 30s（认证域 15s）。

### 1.3 成功响应 envelope

前端类型区分两种形态，后端需按域保持一致：

**A. 法律/数据域** — `{ data, error }`（`error` 成功时为 `null`）：

```json
{ "data": { }, "error": null }
```

分页数据体形态（法律/数据域列表统一使用 `items + limit + offset`）：

```json
{ "data": { "items": [], "limit": 20, "offset": 0 }, "error": null }
```

**B. 共享 envelope 定义**（`types/api.ts`，用于带分页 meta 的接口）：

```jsonc
{
  "data": null,
  "error": null,
  "meta": {
    "request_id": "req_xxx",
    "pagination": { "page": 1, "size": 20, "total": 100, "total_pages": 5 }
  }
}
```

> 说明：法律/数据域列表当前使用 `limit/offset` 平铺形态（见各端点）；`meta.pagination` 的 `page/size/total/total_pages` 结构为共享类型预留，招聘域后端已使用 `page/page_size/total`。后端应在同一域内保持单一风格。

### 1.4 错误响应

前端错误归一化（`http-client.ts`）兼容两种后端错误结构，后端二选一即可：

**结构一（推荐，嵌套 error 对象）**：

```json
{
  "request_id": "req_xxx",
  "error": {
    "code": "AUTH_EXPIRED",
    "message": "登录状态已失效",
    "retryable": false,
    "details": {}
  }
}
```

**结构二（扁平，兼容旧接口）**：

```json
{
  "error_code": "RATE_LIMITED",
  "message": "操作过于频繁",
  "retry_after_seconds": 30,
  "trace_id": "trace_xxx"
}
```

前端最终统一为内部 `ApiError`：`{ error_code, message, details?, retry_after_seconds?, trace_id? }`。

### 1.5 HTTP 状态码 → 错误码映射（`http-client.ts`）

后端未提供 body 错误码时，前端按状态码兜底映射，后端应尽量返回与之一致的语义：

| HTTP | 前端映射 error_code | 前端行为 |
|---:|---|---|
| 401 | `AUTH_EXPIRED` | 触发一次 refresh；失败则清会话跳登录 |
| 403 | `AUTH_FORBIDDEN` | 跳转 `forbidden` 页 |
| 413 | `FILE_TOO_LARGE` | — |
| 422 | `PARSE_FAILED` | — |
| 429 | `RATE_LIMITED` | Toast 提示，读 `retry_after_seconds` |
| 503 | `AGENT_DEPENDENCY_TIMEOUT` | Toast 服务异常 |
| 504 | `LLM_TIMEOUT` | — |
| ≥500 | `AGENT_DEPENDENCY_TIMEOUT` | Toast 服务异常 |
| 请求超时 | `AGENT_DEPENDENCY_TIMEOUT` | — |
| 网络错误 | `NETWORK_ERROR` | Toast 服务异常 |

**前端已知错误码全集**（`API_ERROR_CODES`，后端应从中取值）：
`AUTH_REQUIRED`、`AUTH_EXPIRED`、`AUTH_FORBIDDEN`、`RATE_LIMITED`、`AGENT_DEPENDENCY_TIMEOUT`、`LLM_TIMEOUT`、`FILE_TOO_LARGE`、`FILE_TYPE_UNSUPPORTED`、`FILE_SCAN_FAILED`、`PARSE_FAILED`、`SQL_POLICY_VIOLATION`、`MCP_UNAVAILABLE`、`INPUT_BLOCKED`、`CLASSIFY_FAILED`、`RETRIEVAL_FAILED`、`CITATION_INVALID`、`DB_UNAVAILABLE`。

---

## 2. 认证域 `/api/auth`

来源：`api/auth.ts`、`types/auth.ts`、`config.ts`（`authApi`）。此域前缀无 `/v1`；`authApi` 独立实例，请求头注入 `Authorization`（若已有 token）与 `X-Request-ID`，`withCredentials: true`。

> **后端归属**：由独立服务 `agents/auth-service` 提供（FastAPI，默认端口 **8081**，匹配 `agent-suite-web/vite.config.ts` 的 `/api/auth` 代理目标）。课程 MVP 实现：内存用户 + JWT access + HttpOnly refresh cookie。启动方式见 `agents/auth-service/README.md`；内置账号 `admin@suite.local / Admin@123`（admin）、`user@suite.local / User@12345`（user）。注意：若前端启用 `VITE_ENABLE_DEV_AUTH=true`，会改用内置 `dev-auth-plugin` 而非本服务——联调真实后端时不要启用该开关。

### 2.1 POST `/login`

请求体 `LoginCredentials`：

```jsonc
{
  "email": "user@example.com",
  "password": "••••••",
  "captcha": "可选"
}
```

响应 `AuthSession`（**直接返回，无 envelope 包裹**）：

```json
{ "access_token": "jwt...", "expires_at": "2026-07-05T10:00:00Z" }
```

> refresh token 不在 body，通过 `withCredentials` 的 HttpOnly cookie 下发。

### 2.2 POST `/refresh`

- 无请求体；依赖 cookie 中的 refresh token。
- 响应同 `AuthSession`：`{ access_token, expires_at }`。
- 401 处理链会在收到 401 时自动调用一次本接口。

### 2.3 POST `/logout`

- 无请求体，无响应体（前端不读取返回）。
- 后端应清除 refresh cookie。

### 2.4 POST `/change-password`

请求体 `PasswordChangeInput`：

```json
{
  "current_password": "旧密码",
  "new_password": "新密码",
  "confirm_password": "确认新密码"
}
```

- 无响应体（前端不读取返回）。

### 2.5 GET `/me`

响应 `UserProfile`（**直接返回，无 envelope**）：

```json
{
  "user_id": "内部标识",
  "public_id": "对外公开 ID",
  "email": "user@example.com",
  "display_name": "张三",
  "role": "admin | user",
  "status": "active | disabled",
  "created_at": "2026-07-05T09:00:00Z",
  "updated_at": "2026-07-05T09:00:00Z"
}
```

> `public_id` 后续会被前端作为 `x-user-public-id`（法律域）和 `X-User-Subject`（数据域）请求头回传。

---

## 3. 法律域 `/api/legal/v1`

来源：`api/legal.ts`、`types/legal.ts`。全部使用 `{ data, error }` envelope，请求头含 `x-user-public-id`。

### 3.1 POST `/sessions` — 创建会话

请求 `LegalSessionCreateInput`：

```jsonc
{ "category_code": "labor", "title": "可选，可为 null" }
```

响应 `data: LegalSession`：

```json
{
  "data": {
    "public_id": "sess_xxx",
    "title": "劳动合同咨询",
    "status": "active | archived | deleted",
    "last_message_at": "2026-07-05T09:00:00Z"
  },
  "error": null
}
```

### 3.2 GET `/sessions/{sessionPublicId}/messages` — 消息列表

- Query：`limit?`、`offset?`
- 响应 `data: LegalMessageListData`：

```json
{
  "data": {
    "items": [
      {
        "public_id": "msg_xxx",
        "role": "user | assistant | system",
        "content": "文本内容",
        "citations": [{ "source": "劳动法", "section": "第X条", "snippet": "..." }],
        "high_risk": false,
        "prompt_version": "legal_prompt:v1"
      }
    ],
    "limit": 20,
    "offset": 0
  },
  "error": null
}
```

> `citations` 可为 `null`；`LegalCitation` 允许额外键（`[key: string]: unknown`）。

### 3.3 POST `/sessions/{sessionPublicId}/questions` — 提问（同步应答）

请求 `LegalQuestionInput`：`{ "question": "我的问题" }`

响应 `data: LegalQuestionAnswer`：

```json
{
  "data": {
    "question_message": { "public_id": "msg_q" },
    "answer_message": { "public_id": "msg_a" },
    "answer": "回答正文",
    "citations": [{ "source": "...", "section": "...", "snippet": "..." }],
    "high_risk": false,
    "risk_reason": null,
    "category": "labor",
    "node_trace": ["classify", "retrieve", "answer"]
  },
  "error": null
}
```

### 3.4 GET `/consultation-records` — 咨询记录列表

- Query：`limit?`、`offset?`、`q?`（关键词）
- 响应 `data: LegalConsultationRecordListData`：

```json
{
  "data": {
    "items": [
      {
        "public_id": "rec_xxx",
        "summary": "咨询摘要",
        "citations": [],
        "high_risk": false,
        "disclaimer": "本回答不构成正式法律意见"
      }
    ],
    "limit": 20,
    "offset": 0,
    "query": "关键词 或 null"
  },
  "error": null
}
```

### 3.5 GET `/consultation-records/{recordPublicId}/report` — 咨询报告

响应 `data: LegalReport`：

```json
{
  "data": {
    "record_public_id": "rec_xxx",
    "format": "markdown",
    "content": "# 法律咨询报告\n..."
  },
  "error": null
}
```

### 3.6 POST `/sessions/{sessionPublicId}/messages/{messagePublicId}/feedback` — 消息反馈

请求 `LegalFeedbackInput`：`{ "rating": 5, "comment": "可选，可为 null" }`

响应 `data: LegalFeedback`：`{ "id": 1, "rating": 5, "comment": "..." }`（`id` 可为 `null`）

### 3.7 POST `/sessions/{sessionPublicId}/messages/{messagePublicId}/high-risk-review` — 提交高风险复核

请求 `LegalHighRiskReviewInput`：`{ "reason": "复核原因" }`

响应 `data: LegalHighRiskReview`：

```json
{ "data": { "id": 1, "reason": "复核原因", "status": "pending | reviewed | resolved" }, "error": null }
```

### 3.8 GET `/high-risk-reviews` — 高风险复核列表（Admin）

- Query：`status?`、`limit?`、`offset?`
- 响应 `data: LegalHighRiskReviewListData`：

```json
{
  "data": {
    "items": [
      {
        "id": 1,
        "message_id": 100,
        "user_id": 200,
        "reason": "...",
        "status": "pending",
        "reviewed_by": null,
        "resolution": null
      }
    ],
    "limit": 20,
    "offset": 0,
    "status": "pending"
  },
  "error": null
}
```

### 3.9 POST `/high-risk-reviews/{reviewId}/resolution` — 处理复核（Admin）

- `reviewId` 为数字。
- 请求 `LegalHighRiskReviewResolveInput`：

```json
{ "status": "reviewed | resolved", "resolution": "处理说明" }
```

- 响应 `data: LegalHighRiskReviewAdmin`（同 3.8 items 元素结构）。

---

## 4. 数据问数域 `/api/data/v1`

来源：`api/data-query.ts`、`types/data-query.ts`。使用 `{ data, error }` envelope，请求头含 `X-User-Subject`。分页 Query 为 `limit?`、`offset?`。

### 4.1 GET `/health/live`

响应（无 envelope）：`{ "status": "ok" }`

### 4.2 GET `/health/ready`

响应（无 envelope）`DataHealthReady`：

```json
{ "status": "ok", "db_ok": true, "engine_ready": true, "error": null }
```

### 4.3 POST `/threads` — 创建会话线程

请求 `DataThreadCreateInput`：`{ "title": "可选，可为 null" }`

响应 `data: DataThread`：

```json
{
  "data": {
    "thread_id": "thread_xxx",
    "title": "本月销售分析",
    "status": "active | archived",
    "created_at": "2026-07-05T09:00:00Z",
    "updated_at": "2026-07-05T09:00:00Z"
  },
  "error": null
}
```

### 4.4 GET `/threads` — 线程列表

- Query：`limit?`、`offset?`
- 响应 `data: DataThreadListData`：`{ "items": [DataThread], "limit": 20, "offset": 0 }`

### 4.5 GET `/threads/{threadId}` — 线程详情

响应 `data: DataThread`（同 4.3）。

### 4.6 POST `/threads/{threadId}/runs` — 发起一次问数运行

请求 `DataRunCreateInput`：

```jsonc
{
  "question": "本月各区域销售额是多少？",
  "timezone": "Asia/Shanghai",   // 可选，可为 null
  "locale": "zh-CN",             // 可选，可为 null
  "channel": "web",              // "web" | "feishu"，可选
  "idempotency_key": "可选，可为 null"
}
```

响应 `data: DataRun`：

```json
{
  "data": {
    "run_id": "run_xxx",
    "thread_id": "thread_xxx",
    "status": "pending | running | success | failed | retrying | canceled",
    "question": "本月各区域销售额是多少？",
    "created_at": "2026-07-05T09:00:00Z",
    "started_at": null,
    "finished_at": null
  },
  "error": null
}
```

### 4.7 GET `/runs/{runId}` — 运行详情

响应 `data: DataRunDetail`：

```json
{
  "data": {
    "run_id": "run_xxx",
    "status": "success",
    "error_code": null,
    "error_message": null,
    "created_at": "2026-07-05T09:00:00Z",
    "started_at": "2026-07-05T09:00:01Z",
    "finished_at": "2026-07-05T09:00:05Z"
  },
  "error": null
}
```

### 4.8 POST `/runs/{runId}/cancel` — 取消运行

响应 `data: DataRunDetail`（同 4.7，`status` 应为 `canceled`）。

### 4.9 POST `/runs/{runId}/retry` — 重试运行

响应 `data: DataRunDetail`（同 4.7）。

### 4.10 GET `/query-history` — 查询历史列表

- Query：`limit?`、`offset?`
- 响应 `data: DataQueryHistoryListData`：

```json
{
  "data": {
    "items": [
      {
        "query_id": "q_xxx",
        "status": "success",
        "error_code": null,
        "created_at": "2026-07-05T09:00:00Z",
        "started_at": "2026-07-05T09:00:01Z",
        "finished_at": "2026-07-05T09:00:05Z"
      }
    ],
    "limit": 20,
    "offset": 0
  },
  "error": null
}
```

### 4.11 GET `/query-history/{queryId}` — 查询历史详情

响应 `data: DataQueryHistoryItem`（同 4.10 items 元素）。

### 4.12 GET `/admin/sql-audit` — SQL 审计列表（Admin）

- Query：`limit?`、`offset?`
- 响应 `data: DataAdminSqlAuditListData`：

```json
{
  "data": {
    "items": [
      {
        "audit_id": "audit_xxx",
        "run_id": 100,
        "user_id": 200,
        "decision": "allow | block",
        "sql_fingerprint": "hash",
        "generated_sql": "SELECT ... 或 null",
        "redacted_summary": "脱敏摘要",
        "policy_summary": "命中策略摘要",
        "row_count": 42,
        "result_summary": "结果摘要 或 null",
        "created_at": "2026-07-05T09:00:00Z",
        "expires_at": "2026-07-12T09:00:00Z"
      }
    ],
    "limit": 20,
    "offset": 0
  },
  "error": null
}
```

### 4.13 POST `/integrations/feishu/events` — 飞书事件回调

- 请求头：`X-Feishu-Signature: <签名>`
- 请求 `DataFeishuEventInput`：

```jsonc
{
  "type": "url_verification | event_callback",
  "challenge": "可选，可为 null",
  "header": {},   // 可为 null
  "event": {}     // 可为 null
}
```

- 响应 `data: DataFeishuEventResponse`：

```json
{
  "data": {
    "event_type": "challenge | message",
    "event_id": "evt_xxx 或 null",
    "duplicate": false,
    "challenge": "回显 challenge 或 null"
  },
  "error": null
}
```

### 4.14 GET `/runs/{runId}/stream` — 问数 SSE 流

见 §6。数据域 SSE 由 `dataQueryClient.createRunStream` 发起，URL = `apiBaseUrl + dataPrefix + /runs/{runId}/stream`，携带 `X-User-Subject`。

---

## 5. 招聘域 `/api/recruitment/v1`

来源：`api/recruitment.ts`、`types/recruitment.ts`、招聘后端 schema。前端业务页已全部接线（任务列表/新建/详情+SSE/报告/admin 复核）。

> **envelope 与法律/数据域不同**：招聘域使用 `{ request_id, <资源> }` 形态（无 `data` 包裹），错误为 `{ request_id, error: { code, message, retryable, details } }`（与 §1.4 结构一一致）。列表响应平铺 `items/page/page_size/total`。
>
> 请求头携带 `Authorization`、`X-Request-ID`（与其它非认证域一致）；分页用 `page`（≥1）/ `page_size`（1-100）。

### 5.1 枚举值（来自 `recruit_enums.py`，前后端必须对齐）

| 枚举 | 取值 |
|---|---|
| TaskStatus | `uploaded` `parsing` `parsed` `matching` `reviewing` `completed` `failed` |
| TaskPriority | `normal` `urgent` |
| ReviewStatus | `pending` `approved` `rejected` `changes_requested` |
| ScanStatus | `pending` `clean` `infected` `failed` |
| RunStatus | `pending` `running` `success` `failed` `retrying` `canceled` |

### 5.2 POST `/recruitment-tasks` — 创建任务

请求 `RecruitTaskCreateRequest`：

```jsonc
{
  "title": "后端工程师评估",       // 可选，≤120
  "priority": "normal",            // 默认 normal
  "resume_text": "脱敏简历文本",   // 可选，≤50000
  "jd_text": "岗位说明文本"        // 可选，≤50000
}
```

响应 `201`，`{ request_id, task: RecruitTask }`：

```json
{
  "request_id": "req_xxx",
  "task": {
    "task_id": "task_public_id",
    "title": "后端工程师评估",
    "priority": "normal",
    "status": "uploaded",
    "review_status": "pending",
    "material_summary": {
      "has_resume": true,
      "has_jd": true,
      "resume_material_id": "mat_resume_id",
      "jd_material_id": "mat_jd_id"
    },
    "latest_run_id": null,
    "created_at": "2026-07-05T09:00:00Z"
  }
}
```

### 5.3 GET `/recruitment-tasks` — 任务列表

Query：`page`(≥1)、`page_size`(1-100)、`status`(TaskStatus，alias of `task_status`)、`review_status`(ReviewStatus)。

响应 `{ request_id, items, page, page_size, total }`，`items` 元素结构同 5.2 的 `task`。

### 5.4 GET `/recruitment-tasks/{task_id}` — 任务详情

响应 `{ request_id, task: RecruitTaskDetail }`，详情在任务字段基础上追加 `materials`：

```json
{
  "request_id": "req_xxx",
  "task": {
    "task_id": "task_public_id",
    "title": "...",
    "priority": "normal",
    "status": "completed",
    "review_status": "pending",
    "material_summary": { "has_resume": true, "has_jd": true, "resume_material_id": "...", "jd_material_id": "..." },
    "latest_run_id": "run_public_id",
    "created_at": "2026-07-05T09:00:00Z",
    "materials": [
      {
        "material_id": "mat_resume_id",
        "kind": "resume",
        "scan_status": "clean",
        "original_deleted": true,
        "size_chars": 2400
      }
    ]
  }
}
```

### 5.5 DELETE `/recruitment-tasks/{task_id}` — 软删除

响应 `204`，无 body。

### 5.6 POST `/recruitment-tasks/{task_id}/runs` — 发起分析运行

请求 `RecruitRunStartRequest`（字段均可选，有默认值）：

```jsonc
{ "prompt_version": "recruit_prompt:v1", "workflow_version": "recruitment_workflow:v1" }
```

响应 `202`，`{ request_id, run, stream_url }`：

```json
{
  "request_id": "req_xxx",
  "run": {
    "run_id": "run_public_id",
    "task_id": "task_public_id",
    "thread_id": "thread_public_id",
    "status": "pending",
    "error_code": null,
    "node_trace": [],
    "created_at": "2026-07-05T09:00:00Z",
    "completed_at": null
  },
  "stream_url": "/v1/recruitment-runs/run_public_id/stream"
}
```

### 5.7 GET `/recruitment-runs/{run_id}` — 运行状态

响应 `{ request_id, run: RecruitRun }`（结构同 5.6 的 `run`，`node_trace` 会随执行填充）。

### 5.8 GET `/recruitment-runs/{run_id}/stream` — SSE 流

见 §6。前端由 `recruitmentClient.createRunStream` 发起，URL = `apiBaseUrl + recruitmentPrefix + /recruitment-runs/{run_id}/stream`。后端以标准 SSE 帧下发，事件名见 §6.4，`data` 为 `RecruitmentRunEventPayload` 的 JSON：

```json
{
  "event_id": "evt_xxx",
  "request_id": "req_xxx",
  "run_id": "run_public_id",
  "sequence": 3,
  "timestamp": "2026-07-05T09:00:03Z",
  "payload": { "node_name": "evidence_match", "status": "success" }
}
```

### 5.9 POST `/recruitment-runs/{run_id}/cancel` — 取消运行

无请求体。响应 `{ request_id, run }`，`run.status` 应为 `canceled`。

### 5.10 POST `/recruitment-tasks/{task_id}/reports` — 生成报告

无请求体。任务未通过复核时后端返回 `REVIEW_REQUIRED`（409）。响应 `201`，`{ request_id, report: RecruitReportSummary }`：

```json
{
  "request_id": "req_xxx",
  "report": {
    "report_id": "report_public_id",
    "task_id": "task_public_id",
    "status": "ready",
    "format_available": ["md", "pdf"],
    "expires_at": "2026-07-12T09:00:00Z"
  }
}
```

### 5.11 GET `/recruitment-reports/{report_id}` — 报告详情

响应 `{ request_id, report: RecruitReportDetail }`（在 5.10 摘要基础上追加 `content_markdown`）：

```json
{
  "request_id": "req_xxx",
  "report": {
    "report_id": "report_public_id",
    "task_id": "task_public_id",
    "status": "ready",
    "format_available": ["md", "pdf"],
    "expires_at": "2026-07-12T09:00:00Z",
    "content_markdown": "# 招聘分析报告\n..."
  }
}
```

### 5.12 GET `/recruitment-reports/{report_id}/export` — 导出报告

Query：`format`（`md` | `pdf`，正则 `^(md|pdf)$`）。

响应：文件下载，`Content-Type` 由后端给出，`Content-Disposition: attachment; filename="<filename>"`。前端通过 `recruitmentClient.buildReportExportUrl(reportId, format)` 生成完整 URL（带 `Authorization` 时需注意：导出链接若用浏览器 `<a>` 直点不会带 token——MVP 下 `md` 可直接下载，`pdf` 为 mock 字节）。

### 5.13 GET `/admin/recruitment-tasks/{task_id}` — Admin 任务全貌

响应 `{ request_id, task, latest_run, review }`：

```json
{
  "request_id": "req_xxx",
  "task": { "...": "RecruitTaskDetail，同 5.4" },
  "latest_run": { "...": "RecruitRun，同 5.7；无运行时为 null" },
  "review": {
    "task_id": "task_public_id",
    "review_status": "pending",
    "review_note": null,
    "reviewed_by": "admin_mvp",
    "reviewed_at": "2026-07-05T09:10:00Z"
  }
}
```

> `latest_run` / `review` 可为 `null`。

### 5.14 POST `/admin/recruitment-tasks/{task_id}/review` — Admin 提交复核

请求 `RecruitmentReviewRequest`：

```jsonc
{
  "review_status": "approved",        // pending 之外的状态
  "review_note": "证据充分，可进入面试。"  // 可选，≤1000
}
```

响应 `{ request_id, review: RecruitReview }`（结构同 5.13 的 `review`）。

### 5.15 POST `/admin/match-results/{match_result_id}/override` — 人工覆盖

请求 `RecruitmentManualOverrideRequest`：

```json
{
  "field_path": "match_items[1].match_status",
  "new_value": "partial",
  "reason": "候选人在项目备注中提到了 Kubernetes 运维经验。"
}
```

响应 `{ request_id, override }`：

```json
{
  "request_id": "req_xxx",
  "override": {
    "override_id": "override_public_id",
    "match_result_id": "match_result_public_id",
    "field_path": "match_items[1].match_status",
    "old_value": "no_evidence",
    "new_value": "partial",
    "reason": "候选人在项目备注中提到了 Kubernetes 运维经验。",
    "created_at": "2026-07-05T09:12:00Z"
  }
}
```

### 5.16 招聘域错误码（后端契约）

| code | HTTP | retryable | 说明 |
|---|---:|---:|---|
| `VALIDATION_ERROR` | 422 | false | 请求参数不合法 |
| `TASK_NOT_FOUND` | 404 | false | 任务不存在或无权访问 |
| `MATERIAL_REQUIRED` | 400 | false | 缺少简历或 JD 材料 |
| `FILE_TOO_LARGE` | 413 | false | 文件超限 |
| `FILE_INFECTED` | 400 | false | 安全扫描失败（MVP 由 mock 返回） |
| `UNSUPPORTED_MATERIAL_KIND` | 400 | false | 材料类型不支持 |
| `RUN_NOT_FOUND` | 404 | false | 运行不存在或无权访问 |
| `RUN_ALREADY_ACTIVE` | 409 | true | 同一任务已有运行中任务 |
| `PARSE_FAILED` | 502 | true | Prompt/模板/adapter 调用失败 |
| `FAIRNESS_VIOLATION` | 409 | false | 公平性硬约束失败 |
| `DB_UNAVAILABLE` | 503 | true | 数据库不可用 |
| `REVIEW_REQUIRED` | 409 | false | 报告生成/查看前需 admin 复核 |
| `REPORT_EXPIRED` | 410 | false | 报告已过期 |
| `REPORT_EXPORT_UNAVAILABLE` | 503 | true | 导出 adapter 不可用 |
| `INTERNAL_ERROR` | 500 | false | 未预期错误 |

### 5.17 前端尚未消费的端点/能力

- 契约草案中的 `GET /recruitment-tasks/{task_id}/analysis`（结构化分析结果）**后端未实现**，前端未接；展示用类型 `RecruitmentMatchResult`/`RecruitmentEvidence` 已预留于 `types/agent.ts`，待后端提供后接入。
- 报告列表页 `RecruitReportListPage`、评分规则页 `admin/ScoringAdminPage` 仍为占位（后端无对应列表端点），不影响 MVP 闭环。

---

## 6. SSE 流式协议（法律/数据/招聘通用）

来源：`lib/sse-client.ts`、`types/sse.ts`。

### 6.1 传输方式

- 前端使用 **fetch + ReadableStream**（非原生 EventSource），**GET** 请求，以便携带自定义头。
- 请求头：`Accept: text/event-stream`、`Authorization: Bearer <token>`、`credentials: include`；断线重连时携带 `Last-Event-ID`。
- 数据域额外携带 `X-User-Subject`。

### 6.2 帧格式

标准 SSE 帧，以空行 `\n\n` 分隔，每帧可含：

```text
event: message.delta
id: 42
data: {"...":"JSON"}
```

- `data:` 为 JSON 字符串；前端 `JSON.parse` 后处理。
- `id:` 用于断线续传（写入 `Last-Event-ID`）。
- `event:` 为事件名（见 6.4）。

### 6.3 事件对象结构（`AgentStreamEvent`）

后端 `data` JSON 若包含 `event_id`(string) 且 `sequence`(number)，前端按完整事件处理；否则按最小结构包装。推荐后端直接下发完整结构：

```json
{
  "event_id": "evt_xxx",
  "event": "message.delta",
  "request_id": "req_xxx",
  "run_id": "run_xxx",
  "thread_id": "thread_xxx",
  "sequence": 42,
  "timestamp": "2026-07-05T09:00:03Z",
  "payload": { }
}
```

- **`sequence` 必须单调递增**：前端按 `sequence` 去重，`sequence <= lastSequence` 的事件被丢弃。

### 6.4 事件名与 payload

| event | payload 字段 | 说明 |
|---|---|---|
| `run.started` | — | 运行开始 |
| `node.started` | `node_name`, `metadata?` | 节点开始 |
| `node.completed` | — | 节点完成 |
| `message.delta` | `delta`(string), `cumulative_length?` | 增量文本 |
| `message.completed` | `content`, `citations?`, `high_risk?` | 完整消息 |
| `run.completed` | `citations?`, `high_risk?`, `message_id?` | 运行完成 |
| `run.failed` | `error_code`, `message`, `retryable` | 运行失败 |
| `run.canceled` | — | 运行取消 |
| `heartbeat` | — | 心跳保活 |

> 数据域另有事件名 `node.failed`（`types/data-query.ts` 的 `DataSseContractEvent`）；`payload.citations` 元素为 `{ source, section?, snippet }`，`high_risk` 为 `{ high_risk, reason?, escalation_channel? }`。

### 6.5 心跳与重连

- 前端心跳看门狗默认 **30s**：30s 内无任何帧则判定断线并重连。后端应在空闲时定期下发 `heartbeat` 帧（间隔 < 30s）。
- 重连采用指数退避（基数 1s，上限 8s），最多 **3 次**；超限后进入 `error` 状态。
- 重连时携带 `Last-Event-ID`，后端应据此从该序号之后续传。

---

## 7. 鉴权与会话流程小结

1. `POST /api/auth/login` → 得到 `access_token` + `expires_at`；refresh token 走 HttpOnly cookie。
2. 后续请求头带 `Authorization: Bearer <access_token>`。
3. 收到 `401` → 前端自动 `POST /api/auth/refresh` 续期；成功则重放，失败则清会话跳登录页。
4. `403` → 跳 `forbidden` 页；`429` → 读 `retry_after_seconds` 提示限流。
5. 登录后 `GET /api/auth/me` 拉取 `UserProfile`，其 `public_id` 作为 `x-user-public-id`（法律）/`X-User-Subject`（数据）回传后端。

---

## 8. Admin API 配置中心 `/admin/api-config`（CONFIG-100）

三个 Agent 各自提供同构的 admin 端点，路径前缀沿用各域已有 prefix：

- 法律：`/api/legal/v1/admin/api-config`
- 招聘：`/api/recruitment/v1/admin/api-config`
- 数据：`/api/data/v1/admin/api-config`

### 8.1 通用约定

- 所有端点要求 **admin role**：请求头新增 **`x-user-role: admin`**（前端在 [http-client.ts](agent-suite-web/src/lib/http-client.ts) 注入，与 `x-user-public-id` 同模式）。后端 `AdminUserDep` 校验，非 admin 返回 403 `AUTH_FORBIDDEN`。
- 各域 `api_type` 集合（与该 agent `.env` 依赖一致）：

  | 域 | api_type 集合 |
  |---|---|
  | 法律 | `deepseek`、`embedding`、`vector_db`、`reranker`、`redis` |
  | 招聘 | `deepseek`、`redis` |
  | 数据 | `deepseek`、`mcp`、`redis`、`feishu` |

- **任何响应都不含 `api_key` 原文**，仅返回 `api_key_hint`（如 `sk-t****7890`）。
- 数据库表 `agent_api_config` 在各 agent 自己的库内，结构一致；`api_key_encrypted` 用 Fernet 加密，主密钥来自各 agent 的 `AGENT_CONFIG_ENCRYPTION_KEY` 环境变量（不下发到契约/前端）。
- MVP 阶段（CONFIG-100）：配置仅存储展示，**运行时不热加载**，需重启 agent 才生效；`enabled=false` 当前仅作展示开关。热加载留 CONFIG-200。

### 8.2 GET `/admin/api-config` — 列表

响应 `AgentApiConfigListEnvelope`：

```json
{
  "data": {
    "items": [
      {
        "api_type": "deepseek",
        "display_name": "DeepSeek LLM",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "api_key_hint": "sk-t****7890",
        "timeout_seconds": 60,
        "max_retries": 3,
        "enabled": true,
        "extra": null,
        "updated_by": "usr_xxx",
        "updated_at": "2026-07-05T09:00:00Z"
      }
    ]
  },
  "error": null
}
```

### 8.3 GET `/admin/api-config/{api_type}` — 单条

- `api_type` 不在允许集合或未配置时返回 404 `CONFIG_NOT_FOUND`。
- 响应 `AgentApiConfigEnvelope`（同 8.2 items 元素）。

### 8.4 PUT `/admin/api-config/{api_type}` — 创建或更新（upsert）

请求 `AgentApiConfigUpdate`：

```jsonc
{
  "display_name": "DeepSeek LLM",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "api_key": "sk-xxxxxxxx1234",   // 可选；空字符串/省略 = 不修改现有 key
  "timeout_seconds": 60,
  "max_retries": 3,
  "enabled": true,
  "extra": null
}
```

- `api_key` 提供时：长度 < 8 返回 422 `CONFIG_KEY_TOO_SHORT`；加密入库，仅 `api_key_hint` 入响应。
- `api_key` 省略/空：保留现有 `api_key_encrypted` 不变。
- 响应 `AgentApiConfigEnvelope`（更新后的视图）。

### 8.5 新增错误码

`CONFIG_NOT_FOUND`（404）、`CONFIG_KEY_TOO_SHORT`（422）、`CONFIG_DECRYPT_FAILED`（500）。

---

## 9. 读取的项目规则与 skill（L3 任务合规声明）

- 规则：`.ai-spec/.ai-rules/README.md`、`task-routing.md`、`context-loading.md`。
- Skill：`frontend-web`（前端契约边界、API 集中封装）、`documentation-observability`（API 文档须含请求/响应/错误/示例，契约归档 `docs/contracts/`）。
- 未验证项：认证服务（§2）后端 8 项 smoke test 已通过（login/me/refresh/错误密码/change-password/旧密码失效/logout/cookie 清除）；三业务域（法律/数据/招聘）前端↔后端端点路径已 grep 核对全对齐。尚未做端到端浏览器联调（需同时启动 auth-service + 各业务后端 + 前端 dev server）。
