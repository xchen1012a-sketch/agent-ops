# DATA-300 智能问数 Agent 全模块循环开发计划

## 状态

- 状态：计划已创建，等待进入第一循环实现。
- 模块：`agents/data-query-agent`
- 阶段目标：在已完成 `FOUND-010` 工程基线的基础上，按循环工程完成智能问数 Agent 的数据层、SQL 安全、LangGraph 工作流、API/SSE、审计、评测与飞书适配模块。
- 当前事实来源：
  - `agents/data-query-agent/docs/specification.md`
  - `agents/data-query-agent/docs/detailed-design.md`
  - `agents/data-query-agent/docs/api-contract.md`
  - `agents/data-query-agent/docs/architecture.md`
  - `agents/data-query-agent/README.md`

## 总目标

实现一个可审计、可测试、默认安全的智能问数 Agent，支持 Web 与飞书入口复用同一问数语义，覆盖自然语言提问、意图识别、Schema/指标检索、NL2SQL、SQL AST 安全校验、只读查询执行、结果解释、图表语义、历史审计、评测集与后续飞书消息适配。

## 总范围

### 必做模块

1. 数据字典与指标真源
   - 表/字段/指标/枚举/函数白名单真源。
   - 课件 8 个标准问题基准 SQL。
   - 安全攻击样例与评测集。

2. 运行态数据层
   - 用户镜像、线程、消息、query_runs、node_runs、sql_audits、feedbacks、followup_suggestions、prompt_versions。
   - Alembic migration、ORM、domain entity、repository、application service、测试。

3. SQL 安全策略
   - 单 SELECT 策略。
   - sqlglot AST 解析。
   - 表/列/函数/子句白名单。
   - 禁止写操作、系统 schema、文件函数、延时函数、多语句、注释绕过、UNION。
   - LIMIT、字段数、结果行数、字节数、超时策略。

4. 查询执行适配
   - 只读 MySQL adapter 边界。
   - mock/in-memory query adapter 测试边界。
   - 查询结果结构化表格、截断、错误语义。

5. LangGraph 工作流
   - `input_validation`
   - `intent_classify`
   - `schema_retrieval`
   - `sql_generate`
   - `sql_policy_check`
   - `mcp_execute` / query_execute
   - `result_validate`
   - `interpret`
   - `persist_audit`
   - `polite_refusal`
   - cancel/retry 状态边界。

6. Prompt / LLM 边界
   - Prompt 模板加载。
   - 结构化输出校验。
   - DeepSeek adapter 接口。
   - 默认测试使用 fake adapter，不依赖真实外部服务。

7. Web API / SSE
   - 线程创建/列表。
   - 提问运行创建。
   - 运行详情。
   - SSE 事件契约。
   - 取消/重试。
   - 查询历史。
   - 管理员 SQL 审计。
   - 评测入口。

8. 评测与验收
   - 课件 8 个标准问题。
   - 扩展 30 题评测集。
   - 安全攻击集 100% 拦截。
   - 普通用户不暴露 SQL。
   - 管理员可查看 SQL 审计。

9. 飞书适配
   - 飞书事件入口。
   - 消息去重。
   - 卡片响应投影。
   - 推荐问题按钮。
   - 趋势图表卡片语义。
   - 真实飞书租户凭据不写入仓库。

## 不做事项

- 不在 Prompt 中硬编码完整表结构、指标口径或安全策略；真源必须落在版本化配置/策略文件中。
- 不使用高权限数据库账号执行业务查询。
- 不让 LLM 直接执行 SQL、命令、路径或文件操作。
- 不在普通用户响应中暴露完整 SQL。
- 不提前接真实 DeepSeek、真实 MySQL、真实飞书租户；所有外部服务先有 adapter/fake 边界。
- 不修改法律 Agent、招聘 Agent 或其他模块。
- 不提交其他 AI 的并行改动。

## 循环工程总规则

每个循环固定执行：

1. 明确本循环范围、输入、输出、验收标准、不做事项。
2. 只改 `agents/data-query-agent` 和智能问数计划文档。
3. 先写/补测试，再实现或同步补测试。
4. 运行本循环局部验证。
5. 运行必要质量门禁。
6. 更新本计划和 `docs/plans/current.md`。
7. 只暂存智能问数相关文件。
8. 本地提交。
9. 进入下一循环，除非用户手动打断或触发停止条件。

## 循环清单

### DATA-310：数据字典、指标与 SQL 策略真源

#### 循环 1：Schema/指标/白名单配置骨架

- 目标：建立机器可读真源文件，不接真实数据库。
- 改动范围：
  - `agents/data-query-agent/src/data_query_agent/domain/value_objects/`
  - `agents/data-query-agent/src/data_query_agent/application/services/`
  - `agents/data-query-agent/src/data_query_agent/prompts/` 或 `policies/`
  - 相邻测试。
- 输出：
  - 表/列/函数白名单模型。
  - 指标字典模型。
  - 8 个课件问题基准 SQL fixture。
- 验收：
  - 非法表、非法列、非法函数配置可被拒绝。
  - 8 个标准问题 fixture 可加载。
  - Ruff / MyPy / Pytest 通过。
- 不做：
  - 不连接 `shop_db`。
  - 不做 NL2SQL。

#### 循环 2：SQL 策略模型与资源限制配置

- 目标：把 ADR-0010 的 SQL 安全策略落为可测试模型。
- 输出：
  - `SqlPolicyConfig`
  - `QueryResourceLimits`
  - forbidden keyword/clause 配置。
- 验收：
  - max rows、max fields、max bytes、timeout 有默认值。
  - 禁止项可配置、可测试。

### DATA-320：运行态数据层

#### 循环 3：身份、线程、消息、运行审计首批表

- 目标：建立用户镜像、线程、消息、query_runs、node_runs。
- 输出：
  - domain entities
  - repository port
  - SQLAlchemy ORM
  - Alembic migration
  - application service
  - tests
- 验收：
  - 用户隔离。
  - 线程归属校验。
  - run/node 状态可审计。
  - Alembic 单 head。

#### 循环 4：SQL 审计、反馈、追问、Prompt 版本表

- 目标：补齐 sql_audits、feedbacks、followup_suggestions、prompt_versions。
- 验收：
  - SQL 指纹保存。
  - 审计 90 天过期字段存在。
  - 普通用户与管理员审计边界可区分。
  - prompt version 仅管理员可创建。

### DATA-330：SQL AST 安全校验与查询执行边界

#### 循环 5：sqlglot AST 校验基础

- 目标：实现单 SELECT 解析与白名单校验。
- 输出：
  - `SqlPolicyService`
  - `SqlValidationResult`
  - 安全测试集。
- 验收：
  - SELECT 通过。
  - INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE 被拒绝。
  - 多语句、注释绕过、UNION 被拒绝。
  - 系统 schema 被拒绝。

#### 循环 6：表/列/函数/资源限制完整策略

- 目标：完善 allowed table/column/function/resource limits。
- 验收：
  - 非白名单表/列/函数被拒绝。
  - 无 LIMIT 自动补 LIMIT 或拒绝，按策略确认。
  - 超字段数、超行数、超字节数有错误语义。

#### 循环 7：只读查询 adapter 与 fake query adapter

- 目标：封装真实 MySQL 只读执行边界，同时提供 fake adapter。
- 验收：
  - fake adapter 可支撑工作流和 API 测试。
  - 真实 adapter 不在单测中连接外部数据库。
  - 错误映射覆盖 timeout、connection failed、result too large。

### DATA-340：LangGraph 工作流

#### 循环 8：DataQueryState 与 deterministic 节点

- 目标：建立不依赖 LLM/DB 的 deterministic workflow。
- 输出：
  - state schema
  - nodes
  - graph factory
  - basic tests
- 验收：
  - 非数据问题走 polite_refusal。
  - 数据问题走 schema/sql/policy/execute/interpret 主路径。
  - 节点 trace 完整。

#### 循环 9：工作流 runner、审计、失败语义

- 目标：运行工作流并记录 run/node/audit 边界。
- 验收：
  - 节点 started/finished 记录。
  - SQL_POLICY_VIOLATION 不执行 query adapter。
  - retryable / non-retryable 错误语义可测试。

#### 循环 10：cancel/retry 状态边界

- 目标：实现取消/重试状态投影。
- 验收：
  - cancel 标记 canceled。
  - retry 清理错误状态和节点轨迹。
  - 不实现真实后台队列中断。

### DATA-350：Prompt 与 LLM 边界

#### 循环 11：Prompt 模板加载与输出校验

- 目标：Prompt 文件真源化，结构化输出校验。
- 验收：
  - 缺变量拒绝。
  - 非 JSON / schema 不匹配拒绝。
  - Prompt 不硬编码业务策略。

#### 循环 12：NL2SQL fake adapter 与 prompt-backed 节点

- 目标：把 sql_generate / interpret 改为可注入 LLM adapter。
- 验收：
  - fake adapter 可生成结构化 SQL candidate。
  - 生成结果必须先过 schema，再过 SQL policy。
  - 默认测试不访问真实 DeepSeek。

#### 循环 13：DeepSeek adapter 配置边界

- 目标：实现真实 DeepSeek adapter 的配置和接口边界。
- 验收：
  - 缺配置快速失败。
  - 单测使用 fake HTTP/client。
  - 不提交真实 key。

### DATA-360：Web API 与 SSE

#### 循环 14：线程 API

- 目标：实现线程创建、列表、详情基础契约。
- API：
  - `POST /v1/threads`
  - `GET /v1/threads`
- 验收：
  - 用户隔离。
  - envelope 一致。

#### 循环 15：提问运行 API

- 目标：创建问数 run，返回 pending/running/success 投影。
- API：
  - `POST /v1/threads/{thread_id}/runs`
  - `GET /v1/runs/{run_id}`
- 验收：
  - 普通用户响应不含 SQL。
  - SQL policy blocked 有明确错误。

#### 循环 16：SSE 事件契约

- 目标：冻结前端可消费 SSE 事件。
- API：
  - `GET /v1/runs/{run_id}/stream`
- 验收：
  - run.started、node.started、node.completed、run.completed、run.failed。
  - 不做 token 级真实流式。

#### 循环 17：取消/重试 API

- API：
  - `POST /v1/runs/{run_id}/cancel`
  - `POST /v1/runs/{run_id}/retry`
- 验收：
  - 先做应用层状态变更或 preview。
  - 不接真实任务队列时必须在文档说明。

#### 循环 18：查询历史与详情 API

- API：
  - `GET /v1/query-history`
  - `GET /v1/query-history/{query_id}`
- 验收：
  - 普通用户只能看自己的摘要。
  - 管理员能力不混入普通接口。

#### 循环 19：管理员 SQL 审计 API

- API：
  - `GET /v1/admin/sql-audit`
- 验收：
  - 仅 admin user mirror 可访问。
  - 可查看完整 SQL / policy decision / row_count / result_summary。

### DATA-370：评测与质量

#### 循环 20：课件 8 题评测 harness

- 目标：固化 8 个标准问题、基准 SQL、预期结果入口。
- 验收：
  - 8 题 fixture 可跑。
  - deterministic/fake adapter 模式可验证。

#### 循环 21：扩展 30 题与安全攻击集

- 目标：扩展 TopN、同比/环比、占比、趋势、安全攻击。
- 验收：
  - 安全攻击 100% 拦截。
  - 扩展集记录未接真实 DB 时的未验证项。

#### 循环 22：图表语义与追问推荐

- 目标：趋势类输出 ECharts 语义，返回 followups。
- 验收：
  - 单值问题无图表。
  - 趋势问题返回折线图语义。
  - 排行问题返回柱状图语义。

### FEISHU-500：飞书适配

#### 循环 23：飞书事件入口与签名/去重边界

- 目标：实现飞书事件 API 契约和消息去重。
- API：
  - `POST /v1/integrations/feishu/events`
- 验收：
  - 不依赖真实飞书租户。
  - fixture 验证 challenge / message event。
  - 不提交 secret。

#### 循环 24：飞书卡片响应投影

- 目标：把问数结果转为飞书文本/表格/图表卡片。
- 验收：
  - 推荐问题按钮。
  - 趋势图表卡片语义。
  - 长结果截断。

#### 循环 25：飞书端到端 mock 流程

- 目标：用 fake Feishu client 跑完整入口到响应。
- 验收：
  - 事件去重。
  - 同一 Agent 语义复用 Web workflow。
  - 不访问真实飞书。

### DATA-390：总体验收

#### 循环 26：全量质量门禁

- 验收：
  - Ruff check
  - Ruff format check
  - MyPy
  - Pytest coverage >= 80%
  - Alembic heads 单 head
  - OpenAPI smoke
  - 安全攻击集

#### 循环 27：模块验收记录

- 输出：
  - 更新本计划执行证据。
  - 更新 `docs/plans/current.md`。
  - 记录未接真实 DeepSeek / MySQL / Feishu 的原因。
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

- 需要真实生产库或真实业务数据。
- 需要真实 DeepSeek key、飞书 tenant secret、生产 JWT secret。
- 需要修改法律 Agent、招聘 Agent 或跨模块共享代码。
- 需要改变统一认证边界或数据库权限模型。
- SQL 安全策略与 ADR-0010/0011 冲突。
- 全量验证失败且原因不明。

## 回滚方式

- 每个循环独立本地提交，可按提交回滚。
- 涉及 DB migration 的循环必须提供 downgrade。
- 若真实外部服务不可用，保留 fake adapter 并在验收中标记未接真实服务。
