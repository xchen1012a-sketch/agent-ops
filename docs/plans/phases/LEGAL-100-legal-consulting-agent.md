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
