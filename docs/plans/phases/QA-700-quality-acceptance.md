# QA-700 质量验收与总集成准备

## 状态

- 状态：验收框架已建立；等待前端、智能问数、招聘 Agent 并行任务收口后执行。
- 当前已完成法律 Agent 局部封版复验。
- 本文件只定义验收矩阵和执行顺序，不把未执行项写成通过。

## 目标

为最终交付建立统一质量门禁，覆盖：

1. 三个 Agent 的 lint / format / typecheck / unit / coverage / migration。
2. 前端 typecheck / lint / format / unit / build / E2E。
3. API / SSE 契约兼容。
4. Docker Compose + Nginx 本地集成。
5. 安全、权限、日志脱敏、外部服务降级。
6. 实训演示路径与报告证据。

## 并行开发边界

当前已有三个 AI 并行推进：

| 并行任务 | 目录 | QA 当前动作 |
|---|---|---|
| 前端搭建 | `agent-suite-web/` | 等待收口后执行前端门禁 |
| 智能问数 Agent | `agents/data-query-agent/` | 等待 DATA-300 后续循环完成 |
| 招聘 Agent | `agents/recruitment-assistant-agent/` | 等待 RECRUIT-240/250/260 完成 |

QA 准备阶段不修改这些目录。

## 验收矩阵

### 1. 法律 Agent

| 验收项 | 命令/证据 | 当前状态 |
|---|---|---|
| Ruff lint | `uv run ruff check src tests` | 通过 |
| Ruff format | `uv run ruff format --check src tests` | 通过 |
| MyPy | `uv run mypy src` | 通过，72 source files |
| Unit + coverage | `uv run pytest --cov=legal_consulting_agent -q -p no:cacheprovider` | 通过，133 passed，90% |
| Alembic heads | `uv run alembic heads` | 通过，single head `ceeb31ed5ac6` |
| OpenAPI smoke | `create_app().openapi()` | 通过，28 paths |
| Live DB current | `uv run alembic current` | 未验证：当前无 DB URL |
| Real DeepSeek/RAG | integration test | 未验证：外部服务未接入 |

### 2. 招聘 Agent

| 验收项 | 命令/证据 | 当前状态 |
|---|---|---|
| Ruff / format / MyPy | 模块内命令 | 待执行 |
| Unit + coverage | `uv run pytest --cov=recruitment_assistant_agent` | 待并行任务完成后执行 |
| Alembic heads | `uv run alembic heads` | 待执行 |
| API/SSE | RECRUIT-250 完成后验证 | 未到阶段 |
| 公平性对抗样本 | RECRUIT-260 | 未到阶段 |

### 3. 智能问数 Agent

| 验收项 | 命令/证据 | 当前状态 |
|---|---|---|
| Ruff / format / MyPy | 模块内命令 | 待执行 |
| Unit + coverage | `uv run pytest --cov=data_query_agent` | 待 DATA-300 完成后执行 |
| SQL 安全攻击集 | DATA-300 循环 26 | 未到阶段 |
| 课件 8 题评测 | DATA-300 循环 25 | 未到阶段 |
| API/SSE | DATA-300 循环 18-24 | 未到阶段 |
| Feishu mock | DATA-300 循环 28-30 | 未到阶段 |

### 4. 前端

| 验收项 | 命令/证据 | 当前状态 |
|---|---|---|
| Typecheck | `pnpm typecheck` | 待并行任务完成后执行 |
| Lint | `pnpm lint` | 待执行 |
| Format | `pnpm format:check` | 待执行 |
| Unit | `pnpm test` | 待执行 |
| Build | `pnpm build` | 待执行 |
| E2E | `pnpm e2e` | 业务页完成后执行 |

### 5. 运维与集成

| 验收项 | 命令/证据 | 当前状态 |
|---|---|---|
| Compose config | `docker compose config` | 未验证 |
| Compose up | `docker compose up` | 未验证 |
| Gateway routes | `/api/legal` / `/api/recruitment` / `/api/data` | 未验证 |
| Service degradation | stop one Agent | 未验证 |
| Logs / request id | sample request trace | 未验证 |

## 总集成执行顺序

1. 收敛 Git 工作区：按模块确认 diff，避免并行 AI 改动混线。
2. 单模块门禁：legal → recruitment → data-query → web。
3. 契约检查：三 Agent OpenAPI/SSE 与前端 client 对齐。
4. 本地依赖：MySQL、Redis、Qdrant/BGE、Nginx。
5. Compose 联调：健康检查、主路径 smoke、降级验证。
6. 安全检查：密钥、日志脱敏、SQL 安全、招聘公平性、法律引用。
7. 演示路径：法律 → 招聘 → 问数 → 健康/运维面板。
8. 报告证据：截图、命令输出、风险与未验证项。

## 安全验收清单

| 类别 | 检查点 | 状态 |
|---|---|---|
| Secret | `.env.example` 无真实密钥；真实 `.env` 不入 Git | 待最终扫描 |
| SQL | 智能问数只读账号、SELECT only、白名单、资源限制 | 待 DATA-300 验证 |
| 招聘公平性 | 敏感属性剔除、人工复核、admin 签字 | 待 RECRUIT-260 验证 |
| 法律合规 | 来源引用、高风险审核、免责声明 | 法律本地范围已测；真实 RAG 未验证 |
| 日志 | 不记录完整 Prompt、隐私原文、Token、SQL 全量结果 | 待集成抽查 |
| API 权限 | 401 / 403 / 429 边界 | 待 E2E |

## 阻塞项

- 前端业务页尚在并行开发。
- 智能问数 DATA-300 后半段未完成。
- 招聘 RECRUIT-240/250/260 未完成。
- 真实外部服务凭据和 fixtures 尚未确认。

## 退出标准

QA-700 可标记完成必须满足：

- 所有模块至少完成本地质量门禁，未执行项有明确原因。
- 三条核心演示路径可从 Web 入口访问。
- Docker/Nginx 本地统一入口至少完成 health + 主路径 smoke。
- 安全和隐私清单无红线问题。
- 报告证据可追溯到命令输出或截图。
