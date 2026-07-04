# 智能招聘 API 草案

基础运行接口遵循运维仓 `docs/contracts/api-conventions.md`。

## 领域资源

```text
POST   /v1/recruitment-tasks
GET    /v1/recruitment-tasks
GET    /v1/recruitment-tasks/{task_id}
POST   /v1/recruitment-tasks/{task_id}/resumes
POST   /v1/recruitment-tasks/{task_id}/job-descriptions
PUT    /v1/recruitment-tasks/{task_id}/structured-resume
PUT    /v1/recruitment-tasks/{task_id}/structured-job-description
POST   /v1/recruitment-tasks/{task_id}/runs
GET    /v1/recruitment-reports/{report_id}
POST   /v1/recruitment-reports/{report_id}/export
POST   /v1/recruitment-reports/{report_id}/feedback
```

## 输出原则

报告必须分别返回岗位要求、候选人证据、匹配状态、缺失证据、风险提示和面试问题。不得只返回不可解释的总分。

字段名和 Schema 在 `RECRUIT-210` 固化并生成 OpenAPI，当前仅定义资源边界。

