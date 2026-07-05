# DATA-300 智能问数 Agent 全模块循环开发计划

## 状态

- 状态：计划已按审查意见修订；下一步进入 `DATA-310` 循环 1。
- 模块：`agents/data-query-agent`
- 当前阶段：智能问数 Agent 全模块循环工程。
- 当前执行入口：`docs/plans/current.md` 指向 `DATA-300`。
- 阶段目标：在 `FOUND-010` 工程基线之上，以小步循环完成数据字典、指标真源、SQL 安全策略、运行态数据层、查询执行 adapter、LangGraph 工作流、Prompt/LLM 边界、Web API/SSE、评测与飞书 mock 适配。
- 当前事实来源：
  - `agents/data-query-agent/docs/specification.md`
  - `agents/data-query-agent/docs/detailed-design.md`
  - `agents/data-query-agent/docs/api-contract.md`
  - `agents/data-query-agent/docs/architecture.md`
  - `agents/data-query-agent/README.md`

## 总目标

实现一个可审计、可测试、默认安全的智能问数 Agent。Web 与后续飞书入口复用同一套问数语义，能力覆盖自然语言提问、意图识别、Schema/指标检索、NL2SQL、SQL AST 安全校验、只读查询执行、结果解释、图表语义、历史审计、评测集和飞书消息投影。

## 总范围

### 必做模块

1. 数据字典与指标真源
   - 表、字段、指标、枚举、函数白名单真源。
   - 课件 8 个标准问题基准 SQL fixture。
   - 安全攻击样例与评测集入口。
2. 运行态数据层
   - 用户镜像、线程、消息、query_runs、node_runs、sql_audits、feedbacks、followup_suggestions、prompt_versions。
   - Alembic migration、ORM、domain entity、repository、application service、测试。
3. SQL 安全策略
   - 单 SELECT 策略、sqlglot AST 解析、表/列/函数/子句白名单、资源限制。
   - 禁止写操作、系统 schema、文件函数、延时函数、多语句、注释绕过、UNION。
4. 查询执行适配
   - 只读 MySQL adapter 边界。
   - fake/in-memory query adapter 测试边界。
   - 查询结果结构化表格、截断、错误语义。
5. LangGraph 工作流
   - `input_validation`、`intent_classify`、`schema_retrieval`、`sql_generate`、`sql_policy_check`、`query_execute`、`result_validate`、`interpret`、`persist_audit`、`polite_refusal`。
   - cancel/retry 状态边界、节点 trace、错误投影。
6. Prompt / LLM 边界
   - Prompt 模板加载、结构化输出校验、DeepSeek adapter interface。
   - 默认测试使用 fake adapter，不依赖真实 DeepSeek。
7. Web API / SSE
   - 线程、提问运行、运行详情、SSE、取消/重试、查询历史、管理员 SQL 审计、评测入口。
8. 评测与验收
   - 课件 8 个标准问题。
   - 扩展 30 题评测集。
   - 安全攻击集 100% 拦截。
   - 普通用户不暴露 SQL，管理员可查看 SQL 审计。
9. 飞书 mock 适配
   - 仅完成事件入口、去重、卡片响应投影、推荐问题按钮、趋势图表卡片语义的 mock 边界。
   - 正式飞书租户、密钥、权限和端到端联调仍归属总计划 `FEISHU-500`，不在 `DATA-300` 中接真实租户。

### 不做事项

- 不在 Prompt 中硬编码完整表结构、指标口径或安全策略；真源必须落在版本化配置/策略文件中。
- 不使用高权限数据库账号执行业务查询。
- 不让 LLM 直接执行 SQL、命令、路径或文件操作。
- 不在普通用户响应中暴露完整 SQL。
- 不提前连接真实 DeepSeek、真实 MySQL、真实飞书租户；所有外部服务先有 adapter/fake 边界。
- 不修改法律 Agent、招聘 Agent、统一前端、运维模块或其它无关模块。
- 不提交其它 AI 的并行改动，尤其是 `agents/recruitment-assistant-agent` 与其计划文件。

## 循环工程总规则

每个循环固定执行：

1. 明确本循环目标、输入、输出、验收标准、不做事项。
2. 只改 `agents/data-query-agent` 与智能问数计划文档。
3. 先写或补测试，再实现；无法先测时必须说明原因并补 smoke。
4. 运行本循环最小验证。
5. 运行必要质量门禁；未执行项必须写为“未验证”。
6. 更新本计划的循环状态与验证证据，必要时更新 `docs/plans/current.md` 的 DATA 段。
7. 提交前执行 `git status --short` 与相关 `git diff`，确认没有夹带法律/招聘/其它模块改动。
8. 只暂存智能问数相关文件；禁止 `git add .`。
9. 本地提交，提交信息使用：`feat(data): ...`、`test(data): ...`、`docs(data): ...`。
10. 除非用户手动打断或触发停止条件，继续下一循环。

## 循环清单

### DATA-310：数据字典、指标与 SQL 策略真源

#### 循环 1：Schema / 指标 / 白名单配置骨架

- 目标：建立机器可读真源文件与加载模型，不连接真实数据库。
- 改动范围：
  - `agents/data-query-agent/src/data_query_agent/domain/value_objects/`
  - `agents/data-query-agent/src/data_query_agent/application/services/`
  - `agents/data-query-agent/src/data_query_agent/domain/policies/` 或 `prompts/` 下的版本化资源目录
  - `agents/data-query-agent/tests/unit/`
- 输出：
  - 表/列/函数白名单模型。
  - 指标字典模型。
  - 8 个课件问题基准 SQL fixture。
  - 加载与基础校验测试。
- 验收：
  - 非法表、非法列、非法函数配置可被拒绝。
  - 8 个标准问题 fixture 可加载。
  - Ruff / MyPy / Pytest 通过或明确记录未验证原因。
- 不做：
  - 不连接 `shop_db`。
  - 不做 NL2SQL。
  - 不做 sqlglot AST 校验。

#### 循环 2：SQL 策略模型与资源限制配置

- 目标：把 ADR-0010 的 SQL 安全策略落为可测试模型。
- 输出：`SqlPolicyConfig`、`QueryResourceLimits`、forbidden keyword/clause 配置。
- 验收：max rows、max fields、max bytes、timeout、statement_count 有默认值；禁止项可配置、可测试。

### DATA-320：运行态数据层

> 数据层必须拆小批次；每批只新增一组强相关表、实体、repository port、ORM、migration、service 与测试。不得把所有表塞进一个循环。

#### 循环 3：用户镜像与线程表

- 目标：建立 user mirror 与 thread/session 归属边界。
- 输出：domain entity、repository port、ORM、Alembic migration、application service、测试。
- 验收：用户隔离、线程归属校验、Alembic 单 head。

#### 循环 4：消息表

- 目标：建立线程消息存储与角色枚举。
- 验收：消息按线程归属、分页顺序、角色枚举校验通过。

#### 循环 5：query_runs 与 node_runs

- 目标：记录运行状态和节点 trace。
- 验收：pending/running/success/failed/retrying/canceled 状态可审计，node started/finished 可记录。

#### 循环 6：sql_audits

- 目标：记录 SQL 指纹、策略决策、脱敏摘要和 90 天过期字段。
- 验收：普通用户与管理员审计边界可区分；`expires_at` 存在并可索引。

#### 循环 7：feedbacks 与 followup_suggestions

- 目标：补齐反馈与追问建议持久化。
- 验收：用户只能访问自己的反馈；追问建议可按 run/thread 查询。

#### 循环 8：prompt_versions

- 目标：补齐 Prompt 版本管理表与管理员创建边界。
- 验收：prompt version 仅管理员可创建；业务运行可引用版本号。

### DATA-330：SQL AST 安全校验与查询执行边界

#### 循环 9：sqlglot AST 校验基础

- 目标：实现单 SELECT 解析与基础禁止项拦截。
- 验收：SELECT 通过；INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE、多语句、注释绕过、UNION、系统 schema 被拒绝。

#### 循环 10：表/列/函数白名单完整策略

- 目标：完善 allowed table/column/function/resource limits。
- 验收：非白名单表、列、函数被拒绝；无 LIMIT 的处理策略可测；超字段、超行、超字节有错误语义。

#### 循环 11：只读查询 adapter interface 与 fake query adapter

- 目标：封装真实 MySQL 只读执行边界，同时提供 fake adapter。
- 验收：fake adapter 支撑工作流/API 测试；真实 adapter 不在单测中连接外部数据库；timeout/connection failed/result too large 错误映射覆盖。

### DATA-340：LangGraph 工作流

#### 循环 12：DataQueryState 与 deterministic 节点

- 目标：建立不依赖 LLM/DB 的 deterministic workflow。
- 验收：非数据问题走 polite_refusal；数据问题走 schema/sql/policy/execute/interpret 主路径；节点 trace 完整。

#### 循环 13：workflow runner、审计、失败语义

- 目标：运行工作流并记录 run/node/audit 边界。
- 验收：节点 started/finished 记录；`SQL_POLICY_VIOLATION` 不执行 query adapter；retryable/non-retryable 错误语义可测试。

#### 循环 14：cancel/retry 状态边界

- 目标：实现取消/重试状态投影。
- 验收：cancel 标记 canceled；retry 清理错误状态和节点轨迹；不实现真实后台队列中断。

### DATA-350：Prompt 与 LLM 边界

#### 循环 15：Prompt 模板加载与输出校验

- 目标：Prompt 文件真源化，结构化输出校验。
- 验收：缺变量拒绝；非 JSON/schema 不匹配拒绝；Prompt 不硬编码业务策略。

#### 循环 16：NL2SQL fake adapter 与 prompt-backed 节点

- 目标：把 sql_generate/interpret 改为可注入 LLM adapter。
- 验收：fake adapter 可生成结构化 SQL candidate；生成结果先过 schema 再过 SQL policy；默认测试不访问真实 DeepSeek。

#### 循环 17：DeepSeek adapter 配置边界

- 目标：实现 DeepSeek adapter class、配置校验与 fake HTTP/client 单测。
- 验收：缺配置快速失败；单测使用 fake HTTP/client；不提交真实 key；不跑外网集成测试；默认禁用真实调用。

### DATA-360：Web API 与 SSE

#### 循环 18：线程 API

- API：`POST /v1/threads`、`GET /v1/threads`、`GET /v1/threads/{thread_id}`。
- 验收：用户隔离；统一 envelope；不混入 run 执行逻辑。

#### 循环 19：创建 run API

- API：`POST /v1/threads/{thread_id}/runs`。
- 验收：只创建 pending/run 记录与消息；普通用户响应不含 SQL；不在本循环执行完整 workflow。

#### 循环 20：run 执行与详情 API

- API：`GET /v1/runs/{run_id}`。
- 验收：可触发或投影 workflow 执行结果；SQL policy blocked 有明确错误；状态查询与创建边界清楚。

#### 循环 21：SSE 事件契约

- API：`GET /v1/runs/{run_id}/stream`。
- 验收：`run.started`、`node.started`、`node.completed`、`run.completed`、`run.failed`；不做 token 级真实流式。

#### 循环 22：取消/重试 API

- API：`POST /v1/runs/{run_id}/cancel`、`POST /v1/runs/{run_id}/retry`。
- 验收：先做应用层状态变更或 preview；不接真实任务队列时必须在文档说明。

#### 循环 23：查询历史与详情 API

- API：`GET /v1/query-history`、`GET /v1/query-history/{query_id}`。
- 验收：普通用户只看自己的摘要；管理员能力不混入普通接口。

#### 循环 24：管理员 SQL 审计 API

- API：`GET /v1/admin/sql-audit`。
- 验收：仅 admin user mirror 可访问；可查看完整 SQL/policy decision/row_count/result_summary。

### DATA-370：评测与质量

#### 循环 25：课件 8 题评测 harness

- 目标：固化 8 个标准问题、基准 SQL、预期结果入口。
- 验收：8 题 fixture 可跑；deterministic/fake adapter 模式可验证。

#### 循环 26：扩展 30 题与安全攻击集

- 目标：扩展 TopN、同比、环比、占比、趋势、安全攻击。
- 验收：安全攻击 100% 拦截；未接真实 DB 的项明确标记未验证。

#### 循环 27：图表语义与追问推荐

- 目标：趋势类输出 ECharts 语义，返回 followups。
- 验收：单值问题无图表；趋势问题返回折线图语义；排行问题返回柱状图语义。

### DATA-380：飞书 mock 适配边界

> 本阶段只做智能问数内部 mock 适配，不接真实飞书租户；正式飞书接入仍由总计划 `FEISHU-500` 承接。

#### 循环 28：飞书事件入口与签名/去重边界

- API：`POST /v1/integrations/feishu/events`。
- 验收：不依赖真实飞书租户；fixture 验证 challenge/message event；不提交 secret。

#### 循环 29：飞书卡片响应投影

- 目标：把问数结果转为飞书文本/表格/图表卡片。
- 验收：推荐问题按钮、趋势图表卡片语义、长结果截断。

#### 循环 30：飞书端到端 mock 流程

- 目标：用 fake Feishu client 跑完整入口到响应。
- 验收：事件去重；同一 Agent 语义复用 Web workflow；不访问真实飞书。

### DATA-390：总体验收

#### 循环 31：全量质量门禁

- 验收：Ruff check、Ruff format check、MyPy、Pytest coverage >= 80%、Alembic 单 head、OpenAPI smoke、安全攻击集。

#### 循环 32：模块验收记录

- 输出：
  - 更新本计划执行证据。
  - 更新 `docs/plans/current.md`。
  - 记录未接真实 DeepSeek/MySQL/Feishu 的原因。
  - 标记智能问数 Agent 当前本地计划范围完成。

## 验证命令

在 `agents/data-query-agent` 下执行：

```powershell
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest --cov=data_query_agent -q
uv run alembic heads
```

涉及迁移时补充：

```powershell
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

涉及 OpenAPI 时补充：

```powershell
uv run python -c "from data_query_agent.main import create_app; app=create_app(); print(len(app.openapi()['paths']))"
```

## 停止条件

- 需要真实生产库、真实业务数据、真实 DeepSeek key、飞书 tenant secret 或生产 JWT secret。
- 需要修改法律 Agent、招聘 Agent、统一前端、运维模块或跨模块共享代码。
- 需要改变统一认证边界、数据库权限模型或总计划阶段边界。
- SQL 安全策略与 ADR-0010/ADR-0011 冲突。
- 当前循环最小验证失败且原因不明。
- 发现工作区有并行改动可能被本次提交夹带。

## 回滚方式

- 每个循环独立本地提交，可按提交回滚。
- 涉及 DB migration 的循环必须提供 downgrade。
- 若真实外部服务不可用，保留 fake adapter，并在验收中标记未接真实服务。

## 执行证据

- 2026-07-05：按计划审查结果修订本计划，收紧数据层/API 粒度、飞书 mock 边界、DeepSeek adapter 边界与每循环 Git 暂存/提交门禁。验证：`git diff --check -- docs/plans/phases/DATA-300-data-query-agent.md docs/plans/current.md` 通过。
- 2026-07-05：完成 `DATA-310` 循环 1。新增 Schema/指标/SQL 白名单/8 题基准 SQL fixture 的机器可读真源、加载服务与单元测试；未连接真实 `shop_db`，未做 NL2SQL，未做 sqlglot AST 校验。验证：
  - `uv run pytest tests/unit/test_data_catalog_service.py -q`：6 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：28 passed，coverage 86%。
- 2026-07-05：完成 `DATA-310` 循环 2。新增 `SqlPolicyConfig`、`QueryResourceLimits`、禁止关键字/子句与资源限制配置；未做 sqlglot AST 校验，未连接真实数据库。验证：
  - `uv run pytest tests/unit/test_data_catalog_service.py -q`：9 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：31 passed，coverage 87%。
- 2026-07-05：完成 `DATA-320` 循环 3。新增用户镜像与 query thread/session 数据层切片，包含 domain entity、repository port、SQLAlchemy ORM、Alembic migration、application service 与单元测试；未做消息、run/node、sql_audit，未连接真实数据库。验证：
  - `uv run pytest tests/unit/test_identity_service.py tests/unit/test_identity_models.py tests/unit/test_migrations.py -q`：12 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：39 passed，coverage 81%。
- 2026-07-05：完成 `DATA-320` 循环 4。新增 thread_messages 数据层切片，包含消息角色枚举、消息实体、repository port/implementation、service 方法、ORM、Alembic migration 与单元测试；未做 query_runs、node_runs、sql_audits、API/SSE。验证：
  - `uv run pytest tests/unit/test_identity_service.py tests/unit/test_identity_models.py tests/unit/test_migrations.py -q`：17 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：44 passed，coverage 81%。
- 2026-07-05：完成 `DATA-320` 循环 5。新增 query_runs 与 node_runs 运行状态/节点 trace 数据层切片，包含运行/节点状态枚举、domain entity、repository port/implementation、SQLAlchemy ORM、Alembic migration、application service 与单元测试；未做 sql_audits、feedbacks、API/SSE、LangGraph workflow，未连接真实数据库。验证：
  - `uv run pytest tests/unit/test_run_service.py tests/unit/test_run_models.py tests/unit/test_migrations.py -q`：16 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed（首次发现 `tests/unit/test_run_models.py` 需格式化，已格式化后通过）。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：54 passed，coverage 78%。
- 2026-07-05：完成 `DATA-320` 循环 6。新增 sql_audits SQL 审计数据层切片，包含策略决策枚举、SQL 指纹、原始 SQL/脱敏摘要、策略摘要、结果摘要与 90 天 expires_at；普通用户仅返回脱敏摘要，admin 可查完整审计。未做 feedbacks、API/SSE、workflow runner，未连接真实数据库。验证：
  - `uv run pytest tests/unit/test_audit_service.py tests/unit/test_audit_models.py tests/unit/test_migrations.py -q`：15 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed（首次发现 `tests/unit/test_audit_models.py` 需格式化，已格式化后通过）。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：62 passed，coverage 78%。
- 2026-07-05：完成 `DATA-320` 循环 7。新增 feedbacks 与 followup_suggestions 数据层切片，包含反馈评分枚举、反馈/追问建议实体、repository port/implementation、SQLAlchemy ORM、Alembic migration、application service 与单元测试；验证用户只能查自己的反馈，追问建议可按 run/thread 查询。未做 prompt_versions、API/SSE、workflow，未连接真实数据库。验证：
  - `uv run pytest tests/unit/test_feedback_service.py tests/unit/test_feedback_models.py tests/unit/test_migrations.py -q`：17 passed。
  - `uv run ruff check src tests`：passed（首次发现 2 个 import/format 问题，已 `ruff check --fix` 修复后通过）。
  - `uv run ruff format --check src tests`：passed。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：71 passed，coverage 77%。
- 2026-07-05：完成 `DATA-320` 循环 8。新增 prompt_versions Prompt 版本管理数据层切片，包含 prompt name/version 唯一约束、template hash/body、variables/output schema、active 标记、admin 创建者关联、repository port/implementation、SQLAlchemy ORM、Alembic migration、application service 与单元测试；验证仅 admin 可创建，业务运行可按 name/version 引用版本。未接真实 LLM、未做 API/SSE/workflow。验证：
  - `uv run pytest tests/unit/test_prompt_version_service.py tests/unit/test_prompt_version_models.py tests/unit/test_migrations.py -q`：18 passed。
  - `uv run ruff check src tests`：passed（首次发现 1 个 import/format 问题，已 `ruff check --fix` 修复后通过）。
  - `uv run ruff format --check src tests`：passed。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：80 passed，coverage 77%。
- 2026-07-05：完成 `DATA-330` 循环 9。新增 sqlglot AST 基础安全校验，支持单 SELECT 解析与标准化，拦截 INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE、多语句、注释绕过、UNION、系统 schema 与解析错误；未做完整表/列/函数白名单，未接真实 DB。验证：
  - `uv run pytest tests/unit/test_sql_ast_policy.py -q`：19 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed。
  - `uv run mypy src`：首次发现 sqlglot parse 类型收窄问题，已增加空值校验和 `cast(exp.Expression, ...)` 后 passed。
  - `uv run pytest -q`：99 passed，coverage 78%。
- 2026-07-05：完成 `DATA-330` 循环 10。完善 SQL AST 表/列/函数白名单与资源限制，新增非白名表/列/函数拦截、通配符拦截、LIMIT 必填/max_rows 校验、max_fields 校验、查询结果 row/field/bytes 资源限制错误语义；未做查询 adapter，未连接真实 DB。验证：
  - `uv run pytest tests/unit/test_sql_ast_policy.py -q`：28 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed（首次发现 `tests/unit/test_sql_ast_policy.py` 需格式化，已格式化后通过）。
  - `uv run mypy src`：首次发现列表别名类型收窄问题，已修复后 passed。
  - `uv run pytest -q`：108 passed，coverage 79%。
- 2026-07-05：完成 `DATA-330` 循环 11。新增只读查询 adapter port/DTO、结构化结果、安全错误码与 fake/in-memory query adapter；覆盖成功执行、timeout、connection failed、SQL fixture 未注册、result too large（rows/fields/bytes）映射。未实现真实 MySQL adapter，未连接外部数据库，未做 workflow/API。验证：
  - `uv run pytest tests/unit/test_fake_query_adapter.py -q`：5 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed（首次发现 fake adapter 与测试需格式化，已格式化后通过）。
  - `uv run mypy src`：passed。
  - `uv run pytest -q`：113 passed，coverage 80%。
- 2026-07-05：完成 `DATA-340` 循环 12。新增 DataQueryState/NodeTrace、deterministic 节点与 LangGraph graph factory，打通 input_validation/intent_classify/schema_retrieval/sql_generate/sql_policy_check/query_execute/result_validate/interpret/persist_audit/polite_refusal 主路径；非数据问题走 polite_refusal，数据问题走 deterministic 主路径，节点 trace 完整。未做 runner 审计/失败语义、cancel/retry、API，未调用 LLM/真实 DB。验证：
  - `uv run pytest tests/unit/test_data_query_workflow.py -q`：4 passed。
  - `uv run ruff check src tests`：passed。
  - `uv run ruff format --check src tests`：passed（首次发现 workflow 测试需格式化，已格式化后通过）。
  - `uv run mypy src`：首次发现 Literal 类型收窄问题，已修复后 passed。
  - `uv run pytest -q`：117 passed，coverage 81%。

- 2026-07-05: Completed `DATA-340` cycle 13. Added workflow runner application service for run/node trace, SQL audit, SQL policy, and fake query adapter boundaries. Success path records run started/completed, node started/finished, and `ALLOWED` audit. SQL policy blocked path records `BLOCKED` audit and does not execute query adapter. timeout/connection failed are retryable; result too large is non-retryable. Not included: cancel/retry API, real background queue interruption, real DB/LLM integration. Verification:
  - `uv run pytest tests/unit/test_workflow_runner_service.py -q`: 5 passed.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed after formatting workflow runner and its tests.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 122 passed, coverage 82%.

- 2026-07-05: Completed `DATA-340` cycle 14. Added application-layer cancel/retry state boundaries: `cancel_run` continues to mark runs as `canceled`; `retry_run` clears previous error fields, resets start/finish timestamps, deletes prior node traces, and marks the run as `retrying`. SQLAlchemy repository now exposes explicit retry reset and node-trace cleanup methods. Not included: real background queue interruption, API endpoints, new DB migration, or workflow re-execution scheduling. Verification:
  - `uv run pytest tests/unit/test_run_service.py tests/unit/test_workflow_runner_service.py -q`: 12 passed before formatting.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed after formatting run service/repository files and tests.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 123 passed, coverage 81%.

- 2026-07-05: Completed `DATA-350` cycle 15. Added versioned prompt template resources for `nl2sql` and `interpret_result`, plus `PromptTemplateService` for package-resource loading, declared-variable rendering, and structured JSON output validation. Missing variables, unknown variables, non-JSON output, missing required fields, and type mismatches are rejected before workflow use. Not included: real DeepSeek calls, prompt-backed workflow node replacement, API exposure, or DB prompt version seeding. Verification:
  - `uv run pytest tests/unit/test_prompt_template_service.py -q`: 8 passed before formatting.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed after formatting prompt template service.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 131 passed, coverage 81%.

- 2026-07-05: Completed `DATA-350` cycle 16. Added LLM adapter port/DTOs, deterministic `FakeLlmAdapter`, and prompt-backed workflow node boundary for `sql_generate` and `interpret`. Generated SQL and interpretation outputs are rendered through versioned prompts and must pass structured output validation before entering workflow state; tests cover fake adapter success and malformed LLM output rejection. Not included: real DeepSeek adapter/config, switching the default deterministic graph to LLM mode, API exposure, or external network calls. Verification:
  - `uv run pytest tests/unit/test_prompt_backed_workflow_nodes.py -q`: 4 passed before formatting/type fix.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed after formatting prompt-backed nodes and tests.
  - `uv run mypy src`: passed after narrowing node trace status to Literal.
  - `uv run pytest -q`: 135 passed, coverage 82%.

- 2026-07-05: Completed `DATA-350` cycle 17. Added DeepSeek adapter configuration boundary and injectable HTTP client adapter. Configuration fails fast for missing base URL/API key/model or invalid timeout/retry values; unit tests use fake HTTP responses only and cover success, retry on server error, malformed response rejection, and HTTP error mapping. No real DeepSeek key, no real network integration test, no workflow/API switch to real model. Verification:
  - `uv run pytest tests/unit/test_deepseek_adapter.py -q`: 8 passed before type-wrapper fix.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed after formatting DeepSeek adapter.
  - `uv run mypy src`: passed after wrapping httpx responses behind the internal response protocol.
  - `uv run pytest -q`: 143 passed, coverage 82%.

- 2026-07-05: Completed `DATA-360` cycle 18. Added thread API slice for `POST /v1/threads`, `GET /v1/threads`, and `GET /v1/threads/{thread_id}` with request/response DTOs, subject header dependency, identity service wiring, ownership-scoped access, pagination, and public thread envelopes that do not expose internal user IDs. Synchronized `agents/data-query-agent/docs/api-contract.md` for the thread slice. Not included: run execution logic, workflow trigger, SSE, real auth gateway integration, or frontend wiring. Verification:
  - `uv run pytest tests/unit/test_thread_api.py -q`: 4 passed, 1 Starlette/httpx deprecation warning.
  - `uv run ruff check src tests`: passed after replacing an object-call default in the test fake.
  - `uv run ruff format --check src tests`: passed.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 147 passed, 1 Starlette/httpx deprecation warning, coverage 87%.

- 2026-07-05: Completed `DATA-360` cycle 19. Added `POST /v1/threads/{thread_id}/runs` API slice with request/response DTOs, subject ownership check, user question message creation, and pending query run creation via `QueryRunTraceService`. Response envelope exposes run/thread/status/question only and does not include generated SQL or execute the workflow. Synchronized `agents/data-query-agent/docs/api-contract.md` for run creation. Not included: idempotency dedup implementation, workflow execution, result details, SSE, cancel/retry API, or frontend wiring. Verification:
  - `uv run pytest tests/unit/test_run_api.py -q`: 3 passed, 1 Starlette/httpx deprecation warning.
  - `uv run ruff check src tests`: passed after organizing `test_run_api.py` imports.
  - `uv run ruff format --check src tests`: passed after formatting `test_run_api.py`.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 150 passed, 1 Starlette/httpx deprecation warning, coverage 87%.

- 2026-07-05: Completed `DATA-360` cycle 20. Added `GET /v1/runs/{run_id}` status projection API with ownership-scoped lookup through user mirror and `QueryRunTraceService`; added run detail DTO/envelope and service query helpers. Response exposes run status/error/timestamps only and does not expose generated SQL or trigger workflow execution. Synchronized `agents/data-query-agent/docs/api-contract.md` for run detail. Not included: workflow execution trigger, result table projection, SQL audit details, SSE stream, or frontend wiring. Verification:
  - `uv run pytest tests/unit/test_run_api.py tests/unit/test_run_service.py tests/unit/test_identity_service.py -q`: 19 passed, 1 Starlette/httpx deprecation warning.
  - `uv run ruff check src tests`: passed after organizing `test_run_api.py` imports.
  - `uv run ruff format --check src tests`: passed after formatting `test_run_api.py`.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 152 passed, 1 Starlette/httpx deprecation warning, coverage 87%.

- 2026-07-05: Completed `DATA-360` cycle 21. Added `GET /v1/runs/{run_id}/stream` SSE contract projection for run/node state events: `run.started`, `node.started`, `node.completed`, `node.failed`, `run.completed`, and `run.failed`. Stream access is ownership-scoped through the same run lookup boundary, and the projection intentionally avoids token-level streaming and real queue subscription. Synchronized `agents/data-query-agent/docs/api-contract.md` for SSE event names. Not included: live background worker subscription, token streaming, browser EventSource integration, or frontend wiring. Verification:
  - `uv run pytest tests/unit/test_run_stream_api.py -q`: 3 passed, 1 Starlette/httpx deprecation warning.
  - `uv run ruff check src tests`: passed after organizing `test_run_stream_api.py` imports.
  - `uv run ruff format --check src tests`: passed after formatting `runs.py` and `test_run_stream_api.py`.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 155 passed, 1 Starlette/httpx deprecation warning, coverage 87%.

- 2026-07-05: Completed `DATA-360` cycle 22. Added `POST /v1/runs/{run_id}/cancel` and `POST /v1/runs/{run_id}/retry` API slice with ownership-scoped run lookup. Cancel marks the run as `canceled`; retry uses the existing application-layer retry boundary to clear error/timestamp projection and prepare state for retry. Responses reuse the public run detail envelope and do not expose SQL. Not included: real background queue interruption, workflow re-execution scheduling, browser integration, or frontend wiring. Verification:
  - `uv run pytest tests/unit/test_run_api.py tests/unit/test_run_service.py -q`: 15 passed, 1 Starlette/httpx deprecation warning.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed after formatting `runs.py` and `test_run_api.py`.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 158 passed, 1 Starlette/httpx deprecation warning, coverage 87%.

- 2026-07-05: Completed `DATA-360` cycle 23. Added `GET /v1/query-history` and `GET /v1/query-history/{query_id}` API slice with ownership-scoped run history summaries. List supports `limit`/`offset`; missing user gets an empty list but no detail access. Responses expose public query status/timestamps/error code only and intentionally do not expose generated SQL, SQL policy details, row data, or admin audit fields. Synchronized `agents/data-query-agent/docs/api-contract.md` for query history. Not included: admin SQL audit, frontend wiring, SQL detail projection, or result-table history.
  Verification:
  - `uv run pytest tests/unit/test_query_history_api.py tests/unit/test_run_service.py -q`: 11 passed, 1 Starlette/httpx deprecation warning.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed after formatting query history endpoint and tests.
  - `uv run mypy src`: passed.
  - `uv run pytest -q`: 162 passed, 1 Starlette/httpx deprecation warning, coverage 88%.

- 2026-07-05: Completed `DATA-360` cycle 24. Added admin-only `GET /v1/admin/sql-audit` API slice with `SqlAuditService` dependency wiring and DTO projection for full SQL audit records. Access requires the gateway subject to resolve to a persisted `UserRole.ADMIN` mirror; non-admin and missing user mirrors receive `AUTH_FORBIDDEN`. The endpoint is separated from ordinary query history because it exposes generated SQL, SQL policy decision/details, row count, and result summary for audit/debug use. Synchronized `agents/data-query-agent/docs/api-contract.md` for the admin SQL audit slice. Not included: audit filtering by user/decision/date, CSV export, frontend admin page, or real auth gateway integration.
  Verification:
  - `uv run pytest tests/unit/test_admin_sql_audit_api.py tests/unit/test_audit_service.py -q`: 8 passed, 1 Starlette/httpx deprecation warning.
  - `uv run ruff check src tests`: passed.
  - `uv run ruff format --check src tests`: passed.
  - `uv run mypy src`: passed.
