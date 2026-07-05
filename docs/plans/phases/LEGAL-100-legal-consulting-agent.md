# LEGAL-100 法律咨询 Agent 业务实现

## 状态

进行中。`LEGAL-130 身份与数据层` 六批 11 张表已实现并通过本地验证，等待提交前范围核对。

## 上一阶段

- `FOUND-010 企业级工程基础` 已完成。
- 本地提交：`9286bdd feat(foundation): complete enterprise baseline`
- 工程基线、验证证据和已知技术债记录在 `docs/plans/phases/FOUND-010-enterprise-foundation.md`。

## 用户确认

2026-07-05 用户确认：

1. 切换到 `LEGAL-100`。
2. 第一块先做 `LEGAL-130 身份与数据层`。
3. RAG 和知识库索引放到 `LEGAL-140`。
4. 法律分类先只建表，不预置分类数据，等实际业务分类确定后再插入。

## 目标

实现法律咨询 Agent 的业务能力，覆盖课件要求的会话管理、上下文记忆、历史搜索、密码修改协同、报告导出，并按项目设计增加可审计的 LangGraph 工作流、引用校验、风险提示和质量验收。

## 本阶段范围

- 模块：`agents/legal-consulting-agent`
- 数据库：`legal_agent_db`
- 阶段内按子阶段推进：
  1. `LEGAL-130 身份与数据层`
  2. `LEGAL-140 Agent 工作流`
  3. `LEGAL-150 领域 API 与课件功能`
  4. `LEGAL-160 质量与验收`

## 第一块：LEGAL-130 身份与数据层

### 目标

建立法律咨询 Agent 的持久化业务基础，不连接真实 DeepSeek，不实现 RAG，不预置分类数据。

### 首批表

- `users`：统一认证下的用户镜像；不存密码。
- `legal_categories`：法律分类表；本阶段只建表，不插入预置分类。
- `sessions`：咨询会话。
- `messages`：会话消息。
- `agent_runs`：Agent 运行审计。
- `node_runs`：节点运行审计。

### 执行记录（2026-07-05）

- 已实现集中枚举和值对象：用户角色/状态、会话状态、消息角色、运行状态。
- 已实现领域实体、repository port、SQLAlchemy ORM model、SQLAlchemy repository 和 application service。
- 已通过 Alembic autogenerate 生成迁移：`fcecead92ecd_legal_identity_data_layer.py`。
- 已在本地 Docker MySQL 8.0.36（临时容器 `legal-agent-mysql`，本地端口 3317）验证 `upgrade -> downgrade -> upgrade`。
- 已补充单元测试：ORM metadata、无密码字段、外键/索引、application service 用户镜像/会话/消息/run/node 逻辑。
- 不预置法律分类数据；RAG、知识库索引和真实 DeepSeek 调用仍后置到 `LEGAL-140`。

### 后续表

- `consultation_records`
- `knowledge_materials`
- `prompt_versions`
- `feedbacks`
- `high_risk_reviews`

报告在当前设计中由 `consultation_records` 生成 API 投影，Markdown / PDF 同步临时生成并在响应后删除；本阶段不创建 `reports` / `export_tasks` 表。若后续确认异步批量导出或队列需求，必须先补独立设计再新增迁移。

后续表可在同一 `LEGAL-130` 内分批落地，但每批必须有迁移和测试证据。

### 第二批执行范围：consultation_records

- 目标：持久化一次已完成咨询的结构化快照，供后续历史搜索和报告投影读取。
- 输入：已同步用户、用户所属会话、同一会话中的用户问题消息和助手回答消息。
- 输出：`consultation_records` 领域实体、repository port/实现、ORM、新增 Alembic revision、application service 和相邻测试。
- 约束：用户拥有会话；问题/回答消息属于该会话且角色分别为 `user` / `assistant`；每条回答最多生成一条咨询记录。
- 不做：API/DTO、报告文件生成、RAG、其他后续表、前端和其他 Agent。
- 验收：局部测试、Ruff、MyPy、全量 Pytest、单 Alembic head，以及 MySQL `upgrade -> downgrade -> upgrade`。

### 第二批执行记录（2026-07-05）

- 已新增 `ConsultationRecord` 领域实体、repository port/SQLAlchemy 实现、application service 和 ORM。
- application service 复用现有用户会话隔离，并校验问题/回答属于同一会话且角色分别为 `user` / `assistant`；引用和高风险标记从回答消息生成快照。
- 已通过 Alembic autogenerate 生成迁移：`a89e7df18324_add_consultation_records.py`；未修改历史迁移。
- 首次 MySQL 回滚发现自动生成的逐索引删除与外键支撑索引冲突；新 revision 的 downgrade 已最小调整为直接删除新增表。
- 本地 MySQL 8.0.36 已通过 `upgrade -> downgrade -> upgrade`，当前 revision 为 `a89e7df18324 (head)`。
- `alembic check`：未检测到新的升级操作。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：34 passed，总覆盖率 80%。

### 第三批执行范围：feedbacks

- 目标：保存用户对助手回答的评分和可选文字反馈，为后续回答质量评估提供持久化数据。
- 输入：已同步用户、用户所属会话、同一会话中的助手回答消息、1–5 分评分和可选评论。
- 输出：`Feedback` 领域实体、repository port/实现、ORM、新增 Alembic revision、application service 和相邻测试。
- 约束：用户拥有会话；目标消息属于该会话且角色为 `assistant`；评分范围为 1–5；同一用户对同一消息最多一条反馈。
- 不做：API/DTO、重复反馈的 HTTP 409 映射、前端、工作流、其他后续表及其他 Agent。
- 验收：局部测试、Ruff、MyPy、全量 Pytest、单 Alembic head、schema drift，以及 MySQL `upgrade -> downgrade -> upgrade`。

### 第三批执行记录（2026-07-05）

- 已新增 `Feedback` 领域实体、repository port/SQLAlchemy 实现、application service 和 ORM。
- application service 校验评分范围、用户会话归属，并限制反馈目标为同一会话中的助手消息。
- 数据库通过检查约束保证评分为 1–5，通过唯一约束保证同一用户对同一消息最多一条反馈。
- 已通过 Alembic autogenerate 生成迁移：`d85ad25f66ec_add_feedbacks.py`；未修改历史迁移。
- 新 revision 的 downgrade 直接删除新增表，避免 MySQL 先删除外键支撑索引导致 1553 错误。
- 本地 MySQL 8.0.36 已通过 `upgrade -> downgrade -> upgrade`，当前 revision 为 `d85ad25f66ec (head)`。
- `alembic check`：未检测到新的升级操作。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：39 passed，总覆盖率 80%。

### 第四批执行范围：high_risk_reviews

- 目标：将高风险助手回答持久化到人工审核队列，为后续管理员复核流程提供数据基础。
- 输入：已同步用户、用户所属会话、同一会话中已标记 `high_risk=true` 的助手回答消息和风险原因。
- 输出：审核状态枚举、`HighRiskReview` 领域实体、repository port/实现、ORM、新增 Alembic revision、application service 和相邻测试。
- 约束：用户拥有会话；目标消息属于该会话、角色为 `assistant` 且已标记高风险；新记录状态固定为 `pending`，复核字段为空。
- 不做：管理员认领/复核/解决状态变更、权限校验、API/DTO、工作流接入、前端、其他后续表及其他 Agent。
- 验收：局部测试、Ruff、MyPy、全量 Pytest、单 Alembic head、schema drift，以及 MySQL `upgrade -> downgrade -> upgrade`。

### 第四批执行记录（2026-07-05）

- 已新增 `ReviewStatus` 枚举、`HighRiskReview` 领域实体、repository port/SQLAlchemy 实现、application service 和 ORM。
- application service 校验用户会话归属，并限制入队目标为同一会话中已标记高风险的助手消息。
- 新建记录固定为 `pending`，复核人、解决说明和复核时间保持为空；管理员状态变更留到 `LEGAL-150` 权限/API 阶段。
- 已通过 Alembic autogenerate 生成迁移：`1644fb1c1451_add_high_risk_reviews.py`；未修改历史迁移。
- 本地 MySQL 8.0.36 已通过 `upgrade -> downgrade -> upgrade`，当前 revision 为 `1644fb1c1451 (head)`。
- `alembic check`：未检测到新的升级操作。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：42 passed，总覆盖率 80%。

### 第五批执行范围：prompt_versions

- 目标：持久化可审计的 Prompt 版本元数据，为后续工作流按版本加载模板提供真源。
- 输入：管理员用户、Prompt 名称/版本、相对模板键、变量 schema 和输出 schema。
- 输出：Prompt 状态枚举、`PromptVersion` 领域实体、repository port/实现、ORM、新增 Alembic revision、application service 和相邻测试。
- 约束：仅管理员可创建；新版本固定为 `draft`；`template_key` 必须是无路径穿越的相对 POSIX 键；同一 Prompt 名称和版本唯一。
- 不做：模板文件读写、版本激活/退役、工作流加载、API/DTO、前端、知识材料及其他 Agent。
- 验收：管理员允许路径、普通用户和非法路径拒绝测试、Ruff、MyPy、全量 Pytest、单 Alembic head、schema drift，以及 MySQL `upgrade -> downgrade -> upgrade`。

### 第五批执行记录（2026-07-05）

- 已新增 `PromptStatus` 枚举、`PromptVersion` 领域实体、repository port/SQLAlchemy 实现、application service 和 ORM。
- application service 仅允许管理员创建，且新版本固定为 `draft`。
- `template_key` 仅接受相对 POSIX 键，拒绝绝对路径、路径穿越、Windows 分隔符、盘符和空值；本批不访问文件系统。
- 已通过 Alembic autogenerate 生成迁移：`d12ac236028f_add_prompt_versions.py`；未修改历史迁移。
- 本地 MySQL 8.0.36 已通过 `upgrade -> downgrade -> upgrade`，当前 revision 为 `d12ac236028f (head)`。
- `alembic check`：未检测到新的升级操作。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：50 passed，总覆盖率 80%。

### 第六批执行范围：knowledge_materials 元数据

- 目标：持久化知识材料来源、SHA-256、相对存储键、索引状态和版本，为 `LEGAL-140` 导入与检索提供元数据真源。
- 输入：管理员用户、可选法律分类、标题/来源/章节、SHA-256 和相对 `file_key`。
- 输出：材料状态枚举、`KnowledgeMaterial` 领域实体、repository port/实现、ORM、新增 Alembic revision、application service 和相邻测试。
- 约束：仅管理员可创建；分类码存在时必须有效；SHA-256 必须为 64 位十六进制；`file_key` 必须是无路径穿越的相对 POSIX 键；初始状态为 `indexing`、分块数 0、版本 1。
- 不做：文件上传/读取、正文入库、解析切分、Embedding、Qdrant、状态更新、API/DTO、前端和其他 Agent。
- 验收：管理员允许路径、普通用户/无效分类/非法哈希/非法路径拒绝测试、Ruff、MyPy、全量 Pytest、单 Alembic head、schema drift，以及 MySQL `upgrade -> downgrade -> upgrade`。

### 第六批执行记录（2026-07-05）

- 已新增 `MaterialStatus` 枚举、`KnowledgeMaterial` 领域实体、repository port/SQLAlchemy 实现、application service 和 ORM。
- application service 仅允许管理员创建；可选分类码存在时必须有效。
- SHA-256 必须为 64 位十六进制并规范化为小写；`file_key` 仅接受安全相对 POSIX 键。
- 新记录固定为 `indexing`、分块数 0、版本 1；本批未读写文件或正文。
- 已通过 Alembic autogenerate 生成迁移：`ceeb31ed5ac6_add_knowledge_materials.py`；未修改历史迁移。
- 本地 MySQL 8.0.36 已通过 `upgrade -> downgrade -> upgrade`，当前 revision 为 `ceeb31ed5ac6 (head)`。
- `alembic check`：未检测到新的升级操作。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：56 passed，总覆盖率 80%。

## 不做事项

- 不实现 RAG 检索、Qdrant 索引构建、BGE embedding/reranker 调用。
- 不调用真实 DeepSeek。
- 不连接生产 MySQL 或真实外部服务。
- 不预置法律分类数据。
- 不实现招聘、智能问数或跨 Agent 调用。
- 不在业务代码中硬编码 Prompt、模型名、分类、权限、路径或数据库字段白名单。
- 不让法律 Agent 存储密码；密码修改由统一认证/前端认证能力负责，法律 Agent 只处理 JWT claim 与用户镜像。

## 依赖与延期项

- 课件法律知识库样本暂未提供：不阻塞 `LEGAL-130`。
- 知识材料导入、切分、向量化、Qdrant collection、引用召回和 RAG 评测：延期到 `LEGAL-140`。
- 真实 DeepSeek 调用、流式回答生成和引用校验端到端：延期到 `LEGAL-140` / `LEGAL-150`。
- 初始法律分类：本阶段只建表，不插入；等实际业务分类确认后再通过迁移或种子脚本处理。

## 第二块：LEGAL-140 Agent 工作流

### 第一切片执行范围：workflow/state/mock 边界

- 目标：在不接真实 DeepSeek、Qdrant、BGE、Redis 或数据库写入的条件下，先落地可测试的 LangGraph 工作流边界。
- 输入：`thread_id`、`user_id`、`question`、`prompt_version`、`workflow_version`，测试中可显式注入 `mock_chunks`。
- 输出：`LegalWorkflowState`、节点纯函数、`build_legal_workflow_graph()` 和相邻单元测试。
- 节点：`input_safety`、`classification`、`context_build`、`retrieval`、`generation`、`citation_check`、`risk_check`、`persist`。
- 约束：不调用真实外部服务；`retrieval` 只消费 adapter/mock 边界输入；`generation` 使用确定性占位逻辑；`persist` 只暴露持久化边界，不写数据库。
- 不做：API/DTO、SSE、真实 RAG、知识材料导入/切分、Qdrant/BGE/DeepSeek 调用、节点审计入库、取消/重试 runner、前端和其他 Agent。

### 第一切片执行记录（2026-07-05）

- 已新增 workflow state schema、retrieval chunk/citation 类型、节点纯函数和 LangGraph graph factory。
- 已覆盖 Prompt 注入拦截、无来源免责声明、引用校验失败、高风险标记、adapter 提供 chunks 生成引用、完整 graph 顺序执行。
- 由于课件法律知识库样本缺失，默认路径返回无来源免责声明；测试中通过 `mock_chunks` 验证引用校验边界，不把 mock 当作生产知识库。
- `uv run pytest tests/unit/test_legal_workflow.py -q`：5 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，60 files already formatted。
- `uv run mypy src`：通过，45 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：61 passed，总覆盖率 82%。

### LEGAL-140 下一切片建议

- 节点运行审计集成：把 graph 节点状态映射到 `agent_runs` / `node_runs`，验证失败码和 retryable 语义。
- 重试/失败边界：补 `RETRIEVAL_FAILED`、`LLM_TIMEOUT`、`DB_UNAVAILABLE` 的 runner 层状态流转测试。
- 仍不接真实 Qdrant/BGE/DeepSeek，直到知识库样本和本地服务配置确认。

### 第二切片执行范围：workflow 审计映射

- 目标：把 workflow state / error code 映射到已有 `agent_runs` / `node_runs` 审计模型。
- 输入：`LegalWorkflowState`、节点名、`started_at` / `finished_at` 和已有 `LegalDataService`。
- 输出：`LegalWorkflowAuditService`、`WorkflowErrorMapping`、`map_workflow_error()`，以及节点 started / finished 审计写入边界。
- 约束：不新增数据库表；不改 API / SSE；不接真实 DeepSeek、Qdrant、BGE、Redis；不修改其他 Agent。
- 失败映射：无错误 → `success`；`CLASSIFY_FAILED` / `RETRIEVAL_FAILED` / `LLM_TIMEOUT` / `DB_UNAVAILABLE` / `RATE_LIMITED` → `retrying` 且 `retryable=true`；其他错误如 `INPUT_BLOCKED` / `CITATION_INVALID` → `failed` 且 `retryable=false`。
- 审计最小化：metadata 只记录节点名、事件、retryable、分类、chunks_count、高风险标记；不记录完整 Prompt、完整对话或外部响应。
- 不做：真实 runner、取消/重试 API、节点状态更新 SQL、AgentRun 终态更新、外部服务调用、知识库导入和前端。

### 第二切片执行记录（2026-07-05）

- 已新增 `application/services/workflow_audit_service.py`，保持 `workflows/` 纯流程不直接写数据库。
- 已最小扩展 `LegalDataService.create_node_run()` 参数，支持写入 `finished_at`、`duration_ms`、`error_code` 和 metadata；不改 schema、不改 repository 边界。
- 已覆盖 retryable / non-retryable 错误映射、run 创建、node started 记录、成功 finished 记录、`DB_UNAVAILABLE` retrying 记录。
- `uv run pytest tests/unit/test_workflow_audit_service.py tests/unit/test_legal_workflow.py -q`：10 passed。
- `uv run pytest tests/unit/test_legal_data_service.py -q`：26 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，62 files already formatted。
- `uv run mypy src`：通过，46 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：66 passed，总覆盖率 82%。

### LEGAL-140 下一切片建议

- Runner 层顺序执行：串联 graph 节点、审计 service 和错误中断逻辑。
- 取消/重试入口：先做应用层纯测试，不暴露 HTTP API。
- AgentRun 终态更新需要 repository update 能力；若进入该切片，先确认是否允许扩展 repository port / SQLAlchemy repository。

### 第三切片执行范围：workflow runner 应用边界

- 目标：在不暴露 HTTP API、不接真实外部服务的条件下，提供顺序执行纯节点的应用层 runner。
- 输入：`LegalWorkflowState`、`LegalWorkflowAuditService`、节点规格列表和可注入 clock。
- 输出：`LegalWorkflowRunnerService`、`WorkflowNodeSpec`、`WorkflowRunResult`、`prepare_retry_state()`、`mark_canceled()`。
- 行为：按节点顺序记录 started / finished 审计；每个节点执行后合并 state；遇到 `error_code` 立即停止；取消入口在运行节点前标记 `CANCELED`；重试入口清理 `error_code`、`message_id` 和 `node_trace`。
- 约束：不新增数据库表；不改 API / SSE；不接 DeepSeek、Qdrant、BGE、Redis；不修改其他 Agent；不实现 AgentRun 终态 update。
- 不做：真实异步队列、HTTP cancel/retry API、节点 update SQL、外部服务调用、知识库导入和前端。

### 第三切片执行记录（2026-07-05）

- 已新增 `application/services/workflow_runner_service.py`，串联默认节点序列和审计 service。
- 已支持成功路径顺序执行、`INPUT_BLOCKED` 非重试错误中断、`DB_UNAVAILABLE` retrying 中断、取消入口和重试 state 清理。
- 已将 `CANCELED` 映射到 `RunStatus.CANCELED`。
- `uv run pytest tests/unit/test_workflow_runner_service.py tests/unit/test_workflow_audit_service.py tests/unit/test_legal_workflow.py -q`：15 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，64 files already formatted。
- `uv run mypy src`：通过，47 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：71 passed，总覆盖率 83%。

### LEGAL-140 下一切片建议

- 若要让 `agent_runs` / `node_runs` 从追加记录升级为真实状态更新，需要先扩展 repository port / SQLAlchemy repository，并补迁移无关的 update 测试。
- 若不扩展 repository，则下一步可先做 prompt 模板加载边界或 API/SSE 契约前置设计。

### 第四切片执行范围：Prompt 模板加载边界

- 目标：在不调用真实 LLM、不改 API、不改数据库的条件下，提供版本化 Prompt 模板安全加载与变量渲染边界。
- 输入：`PromptVersion` 元数据、受控 `templates_root`、调用方显式变量。
- 输出：`PromptTemplateLoader`、`PromptRenderResult`、`PromptTemplateError`、`validate_template_key()`、`extract_required_variables()`。
- 行为：校验 `template_key` 为安全相对 POSIX key；阻止绝对路径、路径穿越、Windows 分隔符和盘符；从受控根读取 UTF-8 模板；按 `variables.required` 校验必填变量；渲染 `{variable}` 占位符；返回 prompt 名称、版本、模板 key、渲染内容和输出 schema。
- 约束：不把 Prompt 文案硬编码到业务代码；不读取受控根外文件；不调用 DeepSeek；不改 PromptVersion 表结构；不修改其他 Agent。
- 不做：真实 Prompt 文件落库、Prompt 激活/退役 API、LLM 调用、输出 JSON schema 校验、节点接入。

### 第四切片执行记录（2026-07-05）

- 已新增 `prompts/template_loader.py`，并在 `prompts/__init__.py` 导出安全加载接口。
- 已覆盖正常模板渲染、危险 template key 拒绝、必填变量缺失、模板未知占位符缺失和非法 variables schema。
- `uv run pytest tests/unit/test_prompt_template_loader.py -q`：9 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，66 files already formatted。
- `uv run mypy src`：通过，48 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：80 passed，总覆盖率 84%。

### LEGAL-140 下一切片建议

- Prompt 输出 schema 校验边界：对 mock LLM 输出进行结构化校验，不执行模型输出中的命令、SQL 或路径。
- 或将 `classification` 节点改为消费 Prompt loader + mock LLM adapter，仍不接真实 DeepSeek。

### 第五切片执行范围：Prompt 输出 schema 校验边界

- 目标：在不调用真实 LLM、不接 workflow 节点的条件下，对 Prompt / mock LLM 输出建立结构化校验边界。
- 输入：`PromptVersion.output_schema` 和 raw JSON 字符串或已解析对象。
- 输出：`PromptOutputValidator`、`PromptValidatedOutput`、`PromptOutputValidationError`、`parse_json_object_output()`。
- 行为：解析 raw JSON；要求顶层为 JSON object；校验 `output_schema.type == object`；校验 required 字段；按 properties 中的 `type` 校验 string、boolean、integer、number、object、array、null。
- 约束：不执行模型输出中的命令、SQL 或路径；不接 DeepSeek；不改 API / DB；不修改 workflow 节点；不引入新依赖。
- 不做：完整 JSON Schema 引擎、Prompt 文件真源、真实 LLM adapter、classification 节点接入。

### 第五切片执行记录（2026-07-05）

- 已新增 `prompts/output_validator.py`，并在 `prompts/__init__.py` 导出结构化校验接口。
- 已覆盖 JSON 对象解析、非法 JSON / 非对象拒绝、classification 输出通过、必填字段缺失、字段类型错误和非法 schema。
- `uv run pytest tests/unit/test_prompt_output_validator.py tests/unit/test_prompt_template_loader.py -q`：17 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，68 files already formatted。
- `uv run mypy src`：通过，49 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：88 passed，总覆盖率 83%。

### LEGAL-140 下一切片建议

- 将 `classification` 节点改为消费 Prompt loader + mock LLM adapter + output validator。
- 仍不接真实 DeepSeek；mock adapter 只返回测试用 JSON 字符串，并通过 output validator 后进入 state。

### 第六切片执行范围：Prompt-backed classification 节点

- 目标：让 classification 可通过 Prompt loader + mock LLM adapter + output validator 生成结构化分类结果。
- 输入：`safe_question`、`PromptVersion`、模板文件、mock LLM raw JSON 输出。
- 输出：`LegalClassificationPromptService`、`LegalClassificationResult`、`TextLLMAdapter`、`make_prompt_classification_node()`，以及 `build_legal_workflow_graph(classification_handler=...)` 注入点。
- 行为：渲染 `legal_classification` Prompt；调用注入的文本 LLM adapter；通过 `PromptOutputValidator` 校验输出；将 `category`、`intent`、`legal_entities` 写入 workflow state；输出异常时降级 `category=other` 并设置 `CLASSIFY_FAILED`。
- 约束：不接真实 DeepSeek；不改默认 graph 行为；不改 API / DB；不改其他 Agent。
- 不做：真实 LLM adapter、Prompt 文件真源、classification API、重试 runner 接入。

### 第六切片执行记录（2026-07-05）

- 已新增 `application/services/classification_prompt_service.py`。
- 已支持 Prompt-backed classification node factory，并让 `build_legal_workflow_graph()` 支持注入 classification handler。
- 已覆盖 Prompt 渲染、mock LLM 输出校验、节点 state 更新、非法输出映射 `CLASSIFY_FAILED`、graph 注入执行。
- `uv run pytest tests/unit/test_classification_prompt_service.py tests/unit/test_prompt_output_validator.py tests/unit/test_prompt_template_loader.py -q`：21 passed。
- `uv run mypy src`：通过，50 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：92 passed，总覆盖率 84%。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，70 files already formatted。

### LEGAL-140 下一切片建议

- generation 节点接入 Prompt loader + mock LLM adapter + output validator。
- 仍不接真实 DeepSeek；mock 输出需包含 `{answer: str, citations: list}` 并通过引用校验节点。

### 第七切片执行范围：Prompt-backed generation 节点

- 目标：让 generation 可通过 Prompt loader + mock LLM adapter + output validator 生成结构化回答草稿和引用列表。
- 输入：`safe_question`、`context_messages`、`chunks`、`category`、`PromptVersion`、模板文件、mock LLM raw JSON 输出。
- 输出：`LegalGenerationPromptService`、`LegalGenerationResult`、`make_prompt_generation_node()`，以及 `build_legal_workflow_graph(generation_handler=...)` 注入点。
- 行为：渲染 `legal_generation` Prompt；调用注入的文本 LLM adapter；通过 `PromptOutputValidator` 校验输出；将 `answer_draft`、`citations` 写入 workflow state；非法引用结构映射 `CITATION_INVALID`，并交由后续 `citation_check` 节点继续校验来源一致性。
- 约束：不接真实 DeepSeek；不改默认 graph 行为；不改 API / DB；不改其他 Agent；不绕过引用校验节点。
- 不做：真实 LLM adapter、Prompt 文件真源、generation API、RAG 检索接入、重试 runner 接入。

### 第七切片执行记录（2026-07-05）

- 已新增 `application/services/generation_prompt_service.py`。
- 已支持 Prompt-backed generation node factory，并让 `build_legal_workflow_graph()` 支持注入 generation handler。
- 已覆盖 Prompt 渲染、mock LLM 输出校验、节点 state 更新、非法引用结构映射 `CITATION_INVALID`、graph 注入执行。
- `uv run pytest tests/unit/test_generation_prompt_service.py tests/unit/test_classification_prompt_service.py tests/unit/test_prompt_output_validator.py tests/unit/test_prompt_template_loader.py -q`：25 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，72 files already formatted。
- `uv run mypy src`：通过，51 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：96 passed，总覆盖率 84%。

### LEGAL-140 下一切片建议

- risk_check 节点接入 Prompt loader + mock LLM adapter + output validator。
- 仍不接真实 DeepSeek；mock 输出需包含 `{high_risk: bool, risk_reason: str | null}`，并保持高风险审核入库/API 后置。

### 第八切片执行范围：Prompt-backed risk_check 节点

- 目标：让 risk_check 可通过 Prompt loader + mock LLM adapter + output validator 输出结构化高风险判断。
- 输入：`safe_question`、`validated_answer` / `answer_draft`、`citations`、`category`、`PromptVersion`、模板文件、mock LLM raw JSON 输出。
- 输出：`LegalRiskCheckPromptService`、`LegalRiskCheckResult`、`make_prompt_risk_check_node()`，以及 `build_legal_workflow_graph(risk_check_handler=...)` 注入点。
- 行为：渲染 `legal_risk_check` Prompt；调用注入的文本 LLM adapter；通过 `PromptOutputValidator` 校验 `high_risk` 和 nullable `risk_reason`；高风险时要求 `risk_reason` 非空；模型输出非法时不采信模型结果，fail-closed 标记 `high_risk=true` 和 `risk_reason=risk_check_validation_failed`。
- 约束：不接真实 DeepSeek；不改默认 graph 行为；不改 API / DB；不把高风险审核入库提前接入 workflow；不修改其他 Agent。
- 不做：真实 LLM adapter、Prompt 文件真源、审核 API、`high_risk_reviews` 自动入队、重试 runner 接入。

### 第八切片执行记录（2026-07-05）

- 已新增 `application/services/risk_prompt_service.py`。
- 已支持 Prompt-backed risk_check node factory，并让 `build_legal_workflow_graph()` 支持注入 risk_check handler。
- 已最小扩展 `PromptOutputValidator`，支持字段 `type` 为字符串列表，用于 `["string", "null"]` 这类 nullable 输出；仍不引入完整 JSON Schema 引擎。
- 已覆盖高风险原因、低风险 null reason、非法高风险输出 fail-closed、graph 注入执行。
- `uv run pytest tests/unit/test_risk_prompt_service.py tests/unit/test_prompt_output_validator.py -q`：12 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，74 files already formatted。
- `uv run mypy src`：通过，52 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：100 passed，总覆盖率 85%。

### LEGAL-140 下一切片建议

- 整理 prompt-backed 工作流装配边界：集中组装 classification / generation / risk_check 注入节点，仍只使用 mock adapter 和受控 PromptVersion。
- 真实 DeepSeek、RAG 检索、DB 写入、API/SSE、审核入队继续后置到独立切片。

### 第九切片执行范围：Prompt-backed workflow 装配边界

- 目标：在不接真实外部服务的条件下，将 classification / generation / risk_check 三个 Prompt-backed 节点集中装配为一个可验证 graph factory。
- 输入：显式传入的 `LegalPromptWorkflowPrompts`（classification、generation、risk_check 三个 `PromptVersion`）、受控 `PromptTemplateLoader`、`PromptOutputValidator` 和注入式 `TextLLMAdapter`。
- 输出：`LegalPromptWorkflowFactory`、`LegalPromptWorkflowPrompts`，以及可执行的 prompt-backed `build_legal_workflow_graph()` 编译结果。
- 行为：由 factory 创建三个 prompt service 和 node factory，并通过 graph handler 注入点装配；默认 deterministic graph 不变；测试 adapter 按模板 marker 返回确定 JSON。
- 约束：不接真实 DeepSeek；不读取数据库中的 active prompt；不改 API / DB；不新增依赖；不修改其他 Agent。
- 不做：真实 LLM adapter、PromptVersion repository 查询、Prompt 文件真源管理、API/SSE、审核入队、RAG 检索。

### 第九切片执行记录（2026-07-05）

- 已新增 `application/services/prompt_workflow_factory.py`。
- 已导出 `LegalPromptWorkflowFactory` 和 `LegalPromptWorkflowPrompts`。
- 已覆盖从 PromptVersion + 模板 + routing mock LLM adapter 装配完整 graph，并执行 input_safety → classification → context_build → retrieval → generation → citation_check → risk_check → persist 全链路。
- `uv run pytest tests/unit/test_prompt_workflow_factory.py tests/unit/test_risk_prompt_service.py tests/unit/test_generation_prompt_service.py tests/unit/test_classification_prompt_service.py -q`：13 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，76 files already formatted。
- `uv run mypy src`：通过，53 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：101 passed，总覆盖率 85%。

### LEGAL-140 后续切片建议

- 若继续 `LEGAL-140`：真实 LLM adapter 设计需要单独成片，并通过配置/adapter 接入，不在 workflow node 中硬编码模型名、URL 或 key。
- 若进入 `LEGAL-150`：先冻结 API/SSE 契约，再做会话、问答、历史搜索、反馈、报告导出等课件功能。

## 第三块：LEGAL-150 领域 API 与课件功能

### 第一切片执行范围：会话创建 API 契约

- 目标：在不接真实 DeepSeek/RAG、不新增数据库结构的条件下，对外提供法律咨询会话创建 API。
- 输入：受信任上游身份边界 `x-user-public-id`、`category_code`、可选 `title`。
- 输出：`POST /v1/sessions` 与 `POST /api/legal/v1/sessions`、`LegalSessionCreateRequest`、`LegalSessionResponse`、`LegalSessionCreateEnvelope`。
- 行为：API 层只处理 header、DTO、响应 envelope 和参数校验；业务逻辑仍通过 `LegalDataService.create_session()` 执行；repository 事务仍由 request-scoped session 管理。
- 约束：不实现 JWT 解码或权限体系变更；不新增表/迁移；不做问答执行；不接 DeepSeek、Qdrant、BGE；不修改其他 Agent。
- 不做：会话列表/详情、消息接口、问答 API、SSE、前端页面、真实鉴权网关。

### 第一切片执行记录（2026-07-05）

- 已新增会话 DTO：`api/v1/schemas/legal_sessions.py`。
- 已新增 endpoint：`api/v1/endpoints/legal_sessions.py`，并接入 v1 router。
- 已新增 API dependency：`get_current_user_public_id()`、`get_legal_data_service()`、`CurrentUserPublicIdDep`、`LegalDataServiceDep`。
- 已覆盖成功创建、缺失身份 header 映射 `AUTH_REQUIRED`、非法 `category_code` 返回 422。
- `uv run pytest tests/unit/test_legal_sessions_api.py -q`：3 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，79 files already formatted。
- `uv run mypy src`：通过，55 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：104 passed，总覆盖率 89%。

### LEGAL-150 下一切片建议

- 法律问答入口 API 契约：先打通 user message + mock workflow + assistant message 的应用边界。
- 继续保持真实 DeepSeek、RAG 检索、SSE 流式输出和前端后置到独立切片。

### 第二切片执行范围：法律问答入口 API 契约

- 目标：在不接真实 DeepSeek/RAG/SSE 的条件下，提供同步问答入口 API，打通用户消息持久化、默认 deterministic workflow 执行和助手消息持久化边界。
- 输入：受信任上游身份边界 `x-user-public-id`、`session_public_id`、`question`。
- 输出：`POST /v1/sessions/{session_public_id}/questions` 与 `POST /api/legal/v1/sessions/{session_public_id}/questions`、`LegalQuestionRequest`、`LegalQuestionAnswerResponse`、`LegalQuestionAnswerEnvelope`、`LegalQuestionAnswerService`。
- 行为：先保存用户消息；执行默认 graph；若 `INPUT_BLOCKED` 则返回统一错误；成功后保存助手消息并返回回答、引用、高风险标记、分类和节点轨迹。
- 约束：不接真实 DeepSeek；不接 RAG 检索；不新增 DB 表；不做 SSE；不做审核自动入队；不修改其他 Agent。
- 不做：流式问答、取消/重试 HTTP API、真实 LLM adapter、PromptVersion active 查询、报告导出、前端页面。

### 第二切片执行记录（2026-07-05）

- 已新增 `application/services/question_answer_service.py`，封装 user message → workflow → assistant message 的应用层边界。
- 已新增问答 DTO：`api/v1/schemas/legal_questions.py`。
- 已新增 endpoint：`api/v1/endpoints/legal_questions.py`，并接入 v1 router。
- 已新增 API dependency：`get_legal_question_answer_service()`、`LegalQuestionAnswerServiceDep`。
- 已在 `LegalDataService` 增加 `get_user_mirror()`，用于问答 workflow state 的内部 user id 输入；不改 repository port/DB schema。
- 已覆盖问答成功持久化两条消息、prompt-injection 阻断只保存用户消息、API 成功 envelope、空问题 422。
- `uv run pytest tests/unit/test_question_answer_service.py tests/unit/test_legal_questions_api.py -q`：4 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，84 files already formatted。
- `uv run mypy src`：通过，58 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：108 passed，总覆盖率 90%。

### LEGAL-150 下一切片建议

- 历史咨询记录/消息查询 API：先做只读分页契约，复用已有会话用户隔离边界。
- 流式 SSE、真实 DeepSeek/RAG、报告导出和高风险审核入队继续独立成片。

### 第三切片执行范围：会话消息历史查询 API

- 目标：提供用户所属法律咨询会话的消息历史只读分页查询。
- 输入：受信任上游身份边界 `x-user-public-id`、`session_public_id`、`limit`、`offset`。
- 输出：`GET /v1/sessions/{session_public_id}/messages` 与 `GET /api/legal/v1/sessions/{session_public_id}/messages`、`LegalMessageResponse`、`LegalMessageListData`、`LegalMessageListEnvelope`。
- 行为：API 层处理 query 参数边界；service 校验分页范围并通过 repository 查询用户所属会话消息；repository 按 message id 升序返回。
- 约束：只读；不新增 DB schema；不做全文搜索；不接 RAG/DeepSeek；不修改其他 Agent。
- 不做：咨询记录搜索、报告导出、消息删除/编辑、管理员审核、前端页面。

### 第三切片执行记录（2026-07-05）

- 已扩展 `LegalDataRepository.list_messages_for_user_session()` 和 SQLAlchemy 实现。
- 已新增 `LegalDataService.list_session_messages()`，统一分页边界为 `limit=1..100`、`offset>=0`。
- 已新增消息 DTO：`api/v1/schemas/legal_messages.py`。
- 已新增 endpoint：`api/v1/endpoints/legal_messages.py`，并接入 v1 router。
- 已覆盖 service 用户会话隔离与分页、非法分页拒绝、API 成功 envelope、非法 limit 422。
- `uv run pytest tests/unit/test_legal_data_service.py tests/unit/test_legal_messages_api.py -q`：30 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，87 files already formatted。
- `uv run mypy src`：通过，60 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：112 passed，总覆盖率 90%。

### LEGAL-150 下一切片建议

- 反馈 API 契约：复用 `LegalDataService.create_feedback()`，覆盖评分范围、用户会话隔离和助手消息约束。
- 报告导出、SSE、真实 DeepSeek/RAG、高风险审核入队继续独立成片。

### 第四切片执行范围：反馈 API 契约

- 目标：提供用户对助手回答消息的评分反馈 API。
- 输入：受信任上游身份边界 `x-user-public-id`、`session_public_id`、`message_public_id`、`rating`、可选 `comment`。
- 输出：`POST /v1/sessions/{session_public_id}/messages/{message_public_id}/feedback` 与 `/api/legal/v1` 等价路径、`LegalFeedbackCreateRequest`、`LegalFeedbackResponse`、`LegalFeedbackCreateEnvelope`。
- 行为：API 层校验评分范围和评论长度；业务约束复用 `LegalDataService.create_feedback()`，确保用户会话隔离和目标为助手消息。
- 约束：不改 DB schema；不做重复反馈的 HTTP 409 映射；不修改其他 Agent。
- 不做：反馈列表、反馈修改/删除、管理员统计、前端页面。

### 第四切片执行记录（2026-07-05）

- 已新增反馈 DTO：`api/v1/schemas/legal_feedbacks.py`。
- 已新增 endpoint：`api/v1/endpoints/legal_feedbacks.py`，并接入 v1 router。
- 已覆盖 API 成功 envelope、非法 rating 422。
- `uv run pytest tests/unit/test_legal_feedbacks_api.py -q`：2 passed。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，90 files already formatted。
- `uv run mypy src`：通过，62 source files 无错误。
- `uv run pytest --cov=legal_consulting_agent -q`：114 passed，总覆盖率 90%。

### LEGAL-150 下一切片建议

- 高风险审核入队 API 契约：复用 `LegalDataService.create_high_risk_review()`。
- 报告导出、SSE、真实 DeepSeek/RAG、管理员复核流程继续独立成片。

## 验收标准

### LEGAL-130

- Alembic migration 可升级/回滚。
- ORM Model、API DTO、领域对象和工作流 State 不混用。
- repository 不自行提交事务；事务边界由 application/use case 控制。
- 路由不直接访问 ORM、SQL、DeepSeek 或文件系统。
- `users` 只作为统一认证用户镜像，不保存密码。
- 会话和消息具备用户隔离约束，普通用户不能访问他人资源。
- run / node 审计支持 `pending`、`running`、`success`、`failed`、`retrying`、`canceled` 状态。
- `.env.example` 无真实密钥，关键配置缺失时快速失败。

### LEGAL-100 总体验收

- 课件六项基础功能有 API 与测试证据。
- 流式问答、取消、重试、失败恢复和导出路径可验证。
- 回答引用不伪造来源；无来源时明确免责声明。
- 高风险问题进入提示或审核路径。
- Ruff、MyPy、Pytest、迁移、契约、安全扫描和镜像检查通过或明确记录未验证项。

## 验证命令

在 `agents/legal-consulting-agent` 下执行：

```powershell
ruff check src tests
ruff format --check src tests
mypy src
pytest --cov=legal_consulting_agent
alembic heads
```

涉及迁移时补充：

```powershell
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

没有真实 MySQL 时必须明确记录为“真实 DB 未验证”，不得写成通过。

## 验证证据（2026-07-05）

在 `agents/legal-consulting-agent` 下执行：

```powershell
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest --cov=legal_consulting_agent
uv run alembic heads
uv run alembic current
```

结果：

- Ruff check：通过。
- Ruff format check：通过，56 files already formatted。
- MyPy：通过，42 source files 无错误。
- Pytest：56 passed，覆盖率 80%。
- Alembic heads/current：`ceeb31ed5ac6 (head)`。
- 本地 MySQL upgrade/downgrade：通过。

## 停止条件

- 统一认证边界发生变化。
- 需要法律 Agent 存储密码或跨库访问前端认证表。
- 需要预置法律分类但分类口径未确认。
- 需要提前接入知识库、Qdrant、BGE 或 DeepSeek 才能继续 `LEGAL-130`。
- 数据模型与 `agents/legal-consulting-agent/docs/detailed-design.md` 或 ADR-0007 / ADR-0008 / ADR-0012 冲突。
- 发现需要修改 API 主版本、数据库权限、跨 Agent 边界或部署架构。

## 回滚方式

- 计划阶段：回滚 `current.md` 指向 `FOUND-010`，删除或修订本阶段计划。
- 迁移阶段：每个 Alembic revision 必须提供 downgrade；失败时回退到上一 revision。
- 代码阶段：按 `agents/legal-consulting-agent` 模块独立回滚，不影响招聘、智能问数、前端和运维模块。
