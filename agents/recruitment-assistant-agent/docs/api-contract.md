# 智能招聘 Agent API 契约

基础运行接口遵循运维仓 `docs/contracts/api-conventions.md`：路径版本 `/v1`，JSON UTF-8，公开 ID 不暴露数据库自增主键，错误响应使用统一 envelope，流式接口使用 SSE。

本契约用于 `RECRUIT-250` MVP 实现：功能链路完整、接口命名正式，但真实 DeepSeek、真实 ClamAV、Redis pub/sub、PDF 引擎等外部能力先通过 adapter/mock 边界占位。

## 1. 通用响应

成功响应保留 `request_id`，资源主体按 endpoint 返回。

```json
{
  "request_id": "req_opaque_id",
  "task": {}
}
```

错误响应：

```json
{
  "request_id": "req_opaque_id",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数不合法",
    "retryable": false,
    "details": {}
  }
}
```

`details` 不包含栈、SQL、Prompt、Token、简历原文、JD 原文或完整模型输出。

## 2. 任务与材料 API

### POST `/v1/recruitment-tasks`

创建招聘分析任务，并可一次性提交简历/JD 文本。文件上传在本课程 MVP 中保留 adapter 边界，优先支持文本输入，后续可扩展 multipart。

请求：

```json
{
  "title": "Backend Engineer candidate review",
  "priority": "normal",
  "resume_text": "脱敏简历文本",
  "jd_text": "岗位说明文本"
}
```

响应 `201`：

```json
{
  "request_id": "req_opaque_id",
  "task": {
    "task_id": "task_public_id",
    "title": "Backend Engineer candidate review",
    "status": "pending",
    "review_status": "pending",
    "material_summary": {
      "has_resume": true,
      "has_jd": true,
      "resume_material_id": "mat_resume_id",
      "jd_material_id": "mat_jd_id"
    },
    "created_at": "2026-07-05T09:00:00Z"
  }
}
```

### GET `/v1/recruitment-tasks`

查询当前用户任务列表。课程 MVP 支持基础分页与状态筛选。

Query：`page`、`page_size`、`status`、`review_status`。

响应：

```json
{
  "request_id": "req_opaque_id",
  "items": [
    {
      "task_id": "task_public_id",
      "title": "Backend Engineer candidate review",
      "status": "completed",
      "review_status": "pending",
      "latest_run_id": "run_public_id",
      "created_at": "2026-07-05T09:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### GET `/v1/recruitment-tasks/{task_id}`

返回任务详情、材料元数据、最新运行摘要与可展示结果摘要。

响应：

```json
{
  "request_id": "req_opaque_id",
  "task": {
    "task_id": "task_public_id",
    "title": "Backend Engineer candidate review",
    "status": "completed",
    "review_status": "pending",
    "materials": [
      {
        "material_id": "mat_resume_id",
        "kind": "resume",
        "scan_status": "clean",
        "original_deleted": true
      }
    ],
    "latest_run": {
      "run_id": "run_public_id",
      "status": "success",
      "workflow_version": "recruitment_workflow:v1"
    },
    "result_summary": {
      "overall_tier": "medium",
      "fairness_passed": true,
      "gap_count": 1,
      "interview_question_count": 3
    }
  }
}
```

### DELETE `/v1/recruitment-tasks/{task_id}`

课程 MVP 中执行软删除或状态置为 `canceled/deleted`，不物理清库。

响应 `204`，无 body。

## 3. 分析运行 API

### POST `/v1/recruitment-tasks/{task_id}/runs`

启动一次招聘分析运行。请求 handler 不同步执行真实长任务；MVP 可直接调用 mock runner 或本地 workflow runner，但接口语义保持异步。

请求：

```json
{
  "prompt_version": "recruit_prompt:v1",
  "workflow_version": "recruitment_workflow:v1"
}
```

响应 `202`：

```json
{
  "request_id": "req_opaque_id",
  "run": {
    "run_id": "run_public_id",
    "task_id": "task_public_id",
    "thread_id": "thread_public_id",
    "status": "pending",
    "stream_url": "/v1/recruitment-runs/run_public_id/stream"
  }
}
```

### GET `/v1/recruitment-runs/{run_id}`

返回运行状态、节点轨迹、错误码与结果摘要。

```json
{
  "request_id": "req_opaque_id",
  "run": {
    "run_id": "run_public_id",
    "task_id": "task_public_id",
    "status": "success",
    "error_code": null,
    "node_trace": [
      "file_safety",
      "task_route",
      "resume_parse",
      "jd_parse",
      "evidence_match",
      "fairness_check",
      "gap_question_gen",
      "persist"
    ],
    "result_summary": {
      "overall_tier": "medium",
      "fairness_passed": true
    }
  }
}
```

### GET `/v1/recruitment-runs/{run_id}/stream`

SSE 流。课程 MVP 可用内存/mock 事件源；正式部署再替换 Redis pub/sub。

事件类型：

```text
run.started
node.started
node.completed
node.failed
run.completed
run.failed
run.canceled
heartbeat
```

事件 payload：

```json
{
  "event_id": "evt_opaque_id",
  "request_id": "req_opaque_id",
  "run_id": "run_public_id",
  "sequence": 3,
  "timestamp": "2026-07-05T09:00:03Z",
  "payload": {
    "node_name": "evidence_match",
    "status": "success"
  }
}
```

### POST `/v1/recruitment-runs/{run_id}/cancel`

取消未完成运行。MVP 中可将 run 状态置为 `canceled`；真实 worker 取消后续扩展。

响应：

```json
{
  "request_id": "req_opaque_id",
  "run": {
    "run_id": "run_public_id",
    "status": "canceled"
  }
}
```

## 4. 分析结果 API

### GET `/v1/recruitment-tasks/{task_id}/analysis`

返回结构化分析结果，供前端展示与报告生成使用。

响应：

```json
{
  "request_id": "req_opaque_id",
  "analysis": {
    "task_id": "task_public_id",
    "overall_tier": "medium",
    "jd_structure": {
      "job_title": "Backend Engineer",
      "summary": "Build backend services.",
      "requirements": [
        {
          "requirement_type": "must_have",
          "text": "Python",
          "category": "backend",
          "weight_hint": 0.8
        }
      ]
    },
    "match_items": [
      {
        "requirement": "Python",
        "match_status": "match",
        "evidence_snippet": "Built Python APIs.",
        "skill_category": "backend"
      },
      {
        "requirement": "Kubernetes",
        "match_status": "no_evidence",
        "skill_category": "platform"
      }
    ],
    "fairness": {
      "passed": true,
      "violation_details": []
    },
    "gaps": [
      {
        "gap_description": "No Kubernetes evidence.",
        "suggested_question": "Tell us about Kubernetes operations."
      }
    ],
    "interview_questions": [
      {
        "question_text": "How have you operated Kubernetes in production-like environments?",
        "category": "technical",
        "difficulty": "medium"
      }
    ]
  }
}
```

## 5. Admin 复核与人工覆盖 API

### GET `/v1/admin/recruitment-tasks/{task_id}`

Admin 查看任务完整分析与复核状态。MVP 中通过简单 admin dependency 或 mock role 判断，不扩展完整权限矩阵。

### POST `/v1/admin/recruitment-tasks/{task_id}/review`

Admin 签字复核。

请求：

```json
{
  "review_status": "approved",
  "review_note": "Evidence is sufficient for interview preparation."
}
```

响应：

```json
{
  "request_id": "req_opaque_id",
  "task": {
    "task_id": "task_public_id",
    "review_status": "approved",
    "reviewed_by": "user_public_id",
    "reviewed_at": "2026-07-05T09:10:00Z"
  }
}
```

### POST `/v1/admin/match-results/{match_result_id}/override`

人工覆盖单个匹配字段，保留 override 记录。MVP 只支持 `match_items[index].match_status`、`match_items[index].evidence_snippet`、`overall_tier`。

请求：

```json
{
  "field_path": "match_items[1].match_status",
  "new_value": "partial",
  "reason": "Candidate mentioned Kubernetes operations in project notes."
}
```

响应：

```json
{
  "request_id": "req_opaque_id",
  "override": {
    "override_id": "override_public_id",
    "match_result_id": "match_result_public_id",
    "field_path": "match_items[1].match_status",
    "old_value": "no_evidence",
    "new_value": "partial",
    "reason": "Candidate mentioned Kubernetes operations in project notes."
  }
}
```

## 6. 报告 API

### POST `/v1/recruitment-tasks/{task_id}/reports`

为已完成且已复核任务生成报告。普通用户请求未复核任务返回 `REVIEW_REQUIRED`。

响应 `201`：

```json
{
  "request_id": "req_opaque_id",
  "report": {
    "report_id": "report_public_id",
    "task_id": "task_public_id",
    "status": "ready",
    "format_available": ["md", "pdf"],
    "expires_at": "2026-07-12T09:00:00Z"
  }
}
```

### GET `/v1/recruitment-reports/{report_id}`

返回 Markdown 报告正文与结构化摘要。

```json
{
  "request_id": "req_opaque_id",
  "report": {
    "report_id": "report_public_id",
    "task_id": "task_public_id",
    "content_markdown": "# Recruitment Analysis Report\n...",
    "expires_at": "2026-07-12T09:00:00Z"
  }
}
```

### GET `/v1/recruitment-reports/{report_id}/export?format=md|pdf`

导出报告。MVP 中 `md` 直接返回 Markdown 文件；`pdf` 走 PDF adapter 占位实现，可返回 mock PDF 或声明当前环境未启用。

## 7. 错误码

| code | HTTP | retryable | 说明 |
|---|---:|---:|---|
| `VALIDATION_ERROR` | 422 | false | 请求参数不合法 |
| `TASK_NOT_FOUND` | 404 | false | 任务不存在或无权访问 |
| `MATERIAL_REQUIRED` | 400 | false | 缺少简历或 JD 材料 |
| `FILE_TOO_LARGE` | 413 | false | 文件超过课程约定限制 |
| `FILE_INFECTED` | 400 | false | 文件安全扫描失败；MVP 可由 mock adapter 返回 |
| `UNSUPPORTED_MATERIAL_KIND` | 400 | false | 材料类型不支持 |
| `RUN_NOT_FOUND` | 404 | false | 运行不存在或无权访问 |
| `RUN_ALREADY_ACTIVE` | 409 | true | 同一任务已有运行中任务 |
| `PARSE_FAILED` | 502 | true | Prompt 输出、模板渲染或 adapter 调用失败 |
| `FAIRNESS_VIOLATION` | 409 | false | 检测到敏感属性或公平性硬约束失败 |
| `DB_UNAVAILABLE` | 503 | true | 数据库不可用 |
| `REVIEW_REQUIRED` | 409 | false | 报告生成/查看前需要 admin 复核 |
| `REPORT_EXPIRED` | 410 | false | 报告已过期 |
| `REPORT_EXPORT_UNAVAILABLE` | 503 | true | PDF/导出 adapter 当前不可用 |
| `INTERNAL_ERROR` | 500 | false | 未预期错误，不暴露内部细节 |

## 8. MVP 边界

本阶段做：任务、材料文本、运行、简化 SSE、分析结果、admin 复核、人工覆盖、报告与导出接口闭环。

本阶段不做生产级能力：真实 ClamAV、真实 Redis pub/sub、真实异步队列、完整权限矩阵、真实 PDF 引擎、真实外部文件存储、真实 DeepSeek 付费调用。以上能力保留 adapter 边界和错误码，后续可替换实现。
