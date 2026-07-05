# MVP-003 Prune Hidden Features

## 目标

删除 MVP 中已经隐藏、且不影响保留演示链路的前端功能与对应后端入口，降低代码体量和交互复杂度。

## 删除前盘点

### 可安全删除

- 前端路由与页面：
  - 法律后台：用户权限、法律分类、知识材料、Prompt 版本、高风险审核列表页。
  - 招聘后台：候选材料、评分规则、招聘审计页。
  - 智能问数后台：SQL 审计页。
  - 非 MVP 页面：偏好设置页、前端服务状态页。
- 前端 API client / 类型：
  - 法律高风险审核的后台列表与处理方法；保留“对话页创建人工确认”的方法。
  - 招聘后台复核/人工覆盖 client 方法；后端暂不删，见风险边界。
  - 智能问数后台 SQL 审计 client 方法与前端展示类型。
  - 前端服务状态 lib/types/tests。
- 后端入口：
  - 智能问数 `/admin/sql-audit` 展示 endpoint 与 DTO；保留 SQL audit 持久化服务、模型、仓储，因为问数运行链路仍写审计记录。
  - 法律高风险审核后台 list/resolve endpoint；保留 create endpoint 和 high-risk review 表，因为对话页仍可创建人工确认记录。

### 不直接删除

- API 配置：MVP 主链路保留。
- 飞书事件入口：作业标准要求保留飞书/Dify/MCP 证据链，不能因为无菜单而删。
- 招聘后端 admin review API：当前报告生成要求任务先 `approved`；直接删除会破坏“匹配报告”保留入口。后续若要删，必须先把报告生成改为非管理员审批依赖。
- 法律 category、prompt、knowledge 的领域模型和服务：虽然管理页隐藏，但 category 被会话创建使用，prompt/knowledge 属于 Agent/RAG 设计边界；当前也没有对应公开管理 endpoint 可删。
- 后端 health endpoint：运行和 smoke 仍依赖，不删。

## 范围

- 删除或移除前端隐藏 route、页面、孤儿 API client、孤儿类型和相关单测。
- 精简后端 router 中隐藏 admin endpoint。
- 更新当前阶段和验证记录。

## 不做

- 不改数据库迁移和表结构。
- 不删核心审计、Prompt、知识材料、招聘材料、报告生成、飞书事件和 API 配置链路。
- 不改变登录、权限、SSE、三大保留模块主流程。

## 验收标准

- 前端路由中不再包含已隐藏页面。
- 前端 build/typecheck 不再引用被删除页面和 client 方法。
- 后端保留主链路测试通过；被删 endpoint 的测试同步删除或调整。
- 浏览器侧边栏仍只展示 MVP 主入口。

## 验证记录

- 待执行。

## 回滚方式

- 从 git 恢复被删除页面、路由和 endpoint。
- 恢复对应测试后重新运行前端 build 与后端单测。

## Verification Record 2026-07-05

- Removed hidden frontend routes/pages/client methods/types/tests for legal admin pages, recruitment hidden admin/material pages, data SQL audit page, settings page, and frontend health page.
- Removed data-query admin SQL audit API route, DTO, endpoint test, admin-only dependency helper, application service method, repository port method, SQLAlchemy repository method, and fake repository methods.
- Removed legal high-risk review admin list/resolve API route, DTO, endpoint tests, application service methods, repository port methods, SQLAlchemy repository methods, and service tests. Kept create high-risk review because the visible legal chat page still uses it.
- Kept API config, Feishu event endpoint, backend health endpoints, core SQL audit recording/user summaries, and recruitment backend admin review API because retained MVP flows still depend on them.
- Search verification passed with no hits for removed frontend symbols, data-query admin SQL audit symbols, or legal admin review list/resolve symbols.
- `npm.cmd test -- legal-client data-query-client` passed: 2 files, 13 tests.
- `npm.cmd run typecheck` passed.
- `npm.cmd run build` passed. Warnings only: npm project config warnings, Rollup pure comment warnings from dependency code, generated empty `echarts` chunk, and existing large `element` chunk warning.
- Legal backend pytest passed: `.venv\Scripts\python.exe -m pytest tests\unit\test_legal_reviews_api.py tests\unit\test_legal_data_service.py -q` -> 32 tests. Warnings: Starlette/httpx deprecation and pytest cache write permission.
- Legal backend ruff check for touched files passed.
- Data-query backend pytest passed: `.venv\Scripts\python.exe -m pytest tests\unit\test_audit_service.py tests\unit\test_workflow_runner_service.py -q` -> 9 tests. Warning: pytest cache write permission.
- Data-query backend ruff check for touched files passed.

## Additional Verification 2026-07-05

- Removed the leftover `/admin/sql-audit` sample URL from the generic frontend API error mapping test and the stale recruitment admin comment in frontend recruitment types.
- Final removed-symbol search passed with no hits for deleted frontend hidden-feature symbols, data-query admin SQL audit symbols, or legal high-risk review admin list/resolve symbols.
- `npm.cmd test -- api-error-mapping legal-client data-query-client` passed: 3 files, 20 tests.
- `npm.cmd run typecheck` passed after the final cleanup.
