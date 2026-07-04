---
name: backend-api
description: 设计和实现后端 API。用于 REST/OpenAPI、DTO、错误响应、service/repository 分层、health/ready、CORS、配置和 API smoke。
---

# Backend API

## 目标

设计稳定、可测试、难误用的后端接口。契约先行，边界清楚，错误一致，长任务异步，外部输入只在边界信任前校验。

## 适用场景

- 新增或修改 API endpoint。
- 定义 DTO、OpenAPI、错误响应、分页、筛选。
- 调整 service/repository 分层。
- 增加 health、ready、CORS、配置管理。

## 不适用场景

- 纯 UI 修改。
- 纯数据库迁移但不改 API。
- 外部媒体或 AI gateway 的真实接入细节。

## 最小上下文

1. route/controller。
2. DTO/schema。
3. service/repository。
4. API contract/OpenAPI。
5. 相关测试和启动命令。

## 工作流

1. 先写或确认契约，再实现代码。
2. API 层只处理协议、参数、响应、鉴权和边界校验。
3. service 层做业务编排，repository 层做持久化。
4. 输入 DTO 和输出 DTO 分离；不要把 ORM/internal model 直接暴露给前端。
5. 错误响应使用统一 envelope，500 不泄露堆栈。
6. 列表接口默认考虑分页、排序、筛选。
7. 第三方响应当作不可信输入，必须校验后再使用。
8. request handler 不执行长任务，改为任务队列、worker 或明确 mock。
9. health 和 ready 分开：health 表示进程活着，ready 表示依赖可用。
10. 改 API 时同步 contract、测试和 smoke。

## 推荐响应约定

```json
{
  "data": {},
  "error": null
}
```

错误：

```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数不合法",
    "details": {}
  }
}
```

## 模块边界

- `routes/`、`controllers/` 只处理协议、参数绑定、鉴权入口和响应 envelope。
- `schemas/`、`dto/`、`validators/` 只放输入输出 DTO、校验和序列化；不得放业务查询。
- `services/` 负责业务编排、事务边界和调用 repository/client/worker；不得直接处理 HTTP 响应细节。
- `repositories/`、`dao/` 只访问数据库；不得调用第三方 API、LLM、队列或媒体工具。
- `clients/`、`gateways/` 只封装外部服务协议；返回值必须转成内部 DTO 后再进入 service。
- `workers/`、`jobs/` 只做异步任务执行；不得复用 request handler 作为后台任务主体。
- `config/` 只读配置和环境变量；不得在业务模块散落读取环境变量。
- `errors/`、`middleware/` 统一错误映射、日志、CORS 和请求上下文。
- 文件和模块命名必须来自资源名、业务动作或已确认项目词表，不使用 `utils2`、`temp`、`newApi` 这类临时名。

## 相邻 Skill 触发

- API 字段、分页、筛选或错误 envelope 改变时，同时触发 `frontend-web` 或 `frontend-backend-integration`。
- 新增表、字段、索引、事务或查询模式时，同时触发 `database`。
- 接入真实 LLM、队列、Redis、媒体或外部服务时，同时触发对应 gateway / `ai-workflow` / `media-pipeline` skill。

## 验证清单

- [ ] 每个 endpoint 有输入/输出 DTO。
- [ ] 错误格式一致。
- [ ] 边界输入已校验。
- [ ] 列表接口有分页或明确无需分页的理由。
- [ ] API contract/OpenAPI 已同步。
- [ ] 单测、lint/typecheck、API smoke 已执行或说明原因。

## 输出要求

说明 endpoint、DTO、错误语义、契约更新、兼容性、验证命令、smoke 结果和未验证风险。
## 停止条件

- 需要新增或改变认证、权限、租户隔离但用户未确认。
- 需要修改公开 API 契约且没有同步前端或调用方影响。
- 需要连接真实数据库、Redis、队列或外部服务但用户未确认。
- 错误响应、DTO 或迁移方案不清，继续会造成兼容性风险。
## 强制执行规则

- 遵守 `.ai-rules/skill-contract.md`。
- 本 skill 的工作流、停止条件和验证方式优先于通用建议。


