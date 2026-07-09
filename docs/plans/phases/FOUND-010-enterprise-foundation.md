# FOUND-010 企业级工程基础

## 状态

已完成。工程基线、验证证据和已知技术债已记录，等待用户授权进入业务实现阶段。

## 目标

按照已确认企业标准，为三个FastAPI Agent、统一Vue前端和运维仓建立最小可运行、可测试、可迁移、可容器化的工程基础，并完成一个不含真实业务的健康检查垂直切片。

## 范围

- 三个Agent：src layout、FastAPI应用壳、LangGraph装配入口、Settings、错误、日志、live/ready、SQLAlchemy/Alembic、测试和Docker基础。
- 前端：Vite/Vue3/TypeScript/Element Plus应用壳、路由、配置、错误边界和测试基础。
- 运维：服务命名、镜像规范、非敏感环境模板和独立启动验证。
- 质量：lint、format、type、unit、contract、migration、build和安全扫描命令。

## 不做事项

- 不实现法律、招聘、智能问数业务功能。
- 不连接真实DeepSeek、飞书或生产MySQL。
- 不创建共享业务运行库或跨仓源码依赖。
- 不硬编码地址、密钥、端口、模型或数据库。

## 影响模块

> 单仓模块化（ADR-0006）后，下列模块均在同一 Git 仓库；按模块独立修改、独立验证，提交时按模块拆分 commit。

- `agent-suite-web`
- `agents/legal-consulting-agent`
- `agents/recruitment-assistant-agent`
- `agents/data-query-agent`
- `agent-suite-ops`

每个模块分别修改、分别验证；提交说明按模块记录影响。

## 分阶段执行

1. 固化兼容版本矩阵和许可证检查。
2. 建立三个后端同构骨架，但分别拥有独立包名、配置和测试；仅提供LangGraph factory扩展点，不默认安装Deep Agents。
3. 建立前端应用壳和契约Mock基础。
4. 建立迁移基线与四数据库权限设计，不创建业务表。
5. 建立Docker和健康检查，不统一编排业务依赖。
6. 执行全部工程门禁并记录证据。

## 验收标准

- 每个Agent能独立启动并生成OpenAPI；live/ready语义正确。
- 三个Agent没有互相import或共享运行包。
- AsyncSession按请求/任务隔离；迁移升级/回滚空库通过。
- 前端lint、typecheck、unit和production build通过。
- 每仓Docker镜像以非root运行并有健康检查。
- `.env.example`无真实秘密，关键配置缺失时快速失败。
- 项目规则、禁止硬编码扫描和依赖/许可证检查通过。

## 停止条件

- DESIGN-002未完成或用户未允许开发。
- 框架版本不兼容、许可证不明确或需要废弃API。
- 需要提前实现业务才能让骨架运行。
- 需要修改仓库边界、API主版本、数据库权限或认证架构。

## 回滚

各仓独立回滚本阶段新增骨架文件；迁移基线使用downgrade验证；不删除规格、ADR和计划。未获得用户授权不执行Git提交或推送。

## 验证证据（2026-07-05）

执行人：AI（Claude Code，glm-5.2）。所有命令在 Windows 11 / bash 3.x + uv 0.11.2 + pnpm 11.8.0 + Node 22 + Docker Desktop 环境下执行。

### 后端工程门禁（3 个 Agent 一致）

| 项 | legal-consulting (8101) | recruitment-assistant (8102) | data-query (8103) |
|---|---|---|---|
| `ruff check` | 0 errors | 0 errors | 0 errors |
| `ruff format --check` | 通过 | 通过 | 通过 |
| `mypy src` (strict) | 通过 | 通过 | 通过 |
| `pytest --cov` | 83% 覆盖率，全绿 | 83% 覆盖率，全绿 | 84% 覆盖率，全绿 |
| Alembic `heads` | 单一 `0001_initial_baseline` | 单一 `0001_initial_baseline` | 单一 `0001_initial_baseline` |
| Alembic 离线 upgrade/downgrade | 通过（ScriptDirectory 校验） | 同左 | 同左 |
| Docker 构建 | 成功（python:3.12-slim, UID 1001, tini PID 1, HEALTHCHECK on `/v1/health/live`） | 成功 | 成功（端口修正为 8103） |

### 前端工程门禁（agent-suite-web）

| 项 | 结果 |
|---|---|
| `pnpm lint` | 0 errors 0 warnings（ESLint 9 flat config，含 Vue + TS parser 串联） |
| `pnpm format:check` | All files use Prettier code style |
| `pnpm typecheck` | vue-tsc pass |
| `pnpm test` | 19/19 通过（theme / toast / markdown / api-error-mapping） |
| `pnpm build` | 成功（vue 115kb gzip 44kb，element-plus 898kb 待按需优化） |
| Docker 构建 | 成功（node:22-alpine builder + nginx:1.27-alpine runtime, UID 1001, HEALTHCHECK on `/health/live`） |

### 安全 / 依赖扫描

数据源：pip-audit 2.10.1 + OSV（PyPI JSON API 网络受限，回退 OSV）；pnpm audit（npm registry）。

**后端**（3 个 Agent 共 3 类漏洞）：

| 漏洞 | 影响范围 | 处理 |
|---|---|---|
| asyncmy 0.2.11 (PYSEC-2026-286) | 3 个 Agent | 上游无 fix；MySQL 最小权限账号缓解（ADR-0011），监控上游 |
| chromadb 1.5.9 (PYSEC-2026-311) | data-query-agent | 上游无 fix；内部使用不暴露公网 |
| ecdsa 0.19.2 (CVE-2024-23342) | 3 个 Agent（经 python-jose 间接） | 当前未实际调用 JWT；业务实现阶段评估切换 PyJWT 或限制算法至 HS256/RS256 |

**前端**（agent-suite-web 共 6 个漏洞：4 moderate / 1 high / 1 critical）：

| 漏洞 | 严重性 | 处理 |
|---|---|---|
| vitest < 3.2.6 (GHSA-5xrq-8626-4rwp) | critical | WEB-400 阶段升 major v2→v3 |
| vite ≤ 6.4.2 (GHSA-fx2h-pf6j-xcff) | high | WEB-400 阶段升 major v5→v6 |
| vite ≤ 6.4.1 (GHSA-4w7w-66w2-5vf9, path traversal) | moderate | 同上 |
| vite ≤ 6.4.2 (GHSA-v6wh-96g9-6wx3) | moderate | 同上 |
| esbuild ≤ 0.24.2 (GHSA-67mh-4wv8-2f99, dev CSRF) | moderate | 随 vite 升级（dev only） |
| echarts < 6.1.0 (GHSA-fgmj-fm8m-jvvx, XSS) | moderate | WEB-400 阶段升 major v5→v6 |

**为何不在 FOUND-010 修复前端漏洞**：vite / vitest / echarts 三项均为 major version 升级，存在 breaking changes，需配合测试与视觉回归统一完成。FOUND-010 范围限定为「最小可运行骨架」（见「范围」section），major 升级纳入 WEB-400 阶段执行。

### `.env.example` 检查

3 个后端仓 + 1 个前端仓均通过：无真实密钥，关键配置（`JWT_SECRET >= 32 bytes`、`DATABASE_URL`、`DEEPSEEK_API_KEY`、`REDIS_URL`、`DEEPSEEK_API_BASE` 等）启动时校验。

### Docker 容器运行验证（2026-07-05 补充，原仅 `docker build`，未跑 `docker run`）

镜像独立运行（不依赖 docker-compose override）+ HEALTHCHECK 实际生效：

| Agent | image tag | docker run + curl `/v1/health/live` | docker inspect `State.Health.Status` |
|---|---|---|---|
| legal-consulting | `legal-agent:p2-verify` | HTTP 200 | healthy |
| recruitment-assistant | `recruitment-agent:p2-verify` | HTTP 200 | healthy |
| data-query | `data-query-agent:p2-verify` | HTTP 200 | healthy |
| agent-suite-web | `suite-web:p1-verify` | HTTP 200（`/health/live` nginx 本地路由） | healthy |

启动用占位 env（不连真实 DB/DeepSeek，因为 `/v1/health/live` 不触发依赖检查）：
`JWT_SECRET`（≥32 bytes）、`DATABASE_URL`、`DEEPSEEK_API_KEY`、（仅 data-query）`SHOP_DB_READ_URL`。

### 服务地址硬编码移除（2026-07-05 补充）

`agents/*/src/*/core/config.py` 内 `redis_url` / `deepseek_api_base` / `embedding_base_url` / `rag_vector_db_url` / `rag_reranker_base_url` 默认值清空，加入 `validate_required()` 强制校验。验证：

| Agent | 缺 env 启动 | 带齐 env 启动 |
|---|---|---|
| legal | `RuntimeError: REDIS_URL is required; DEEPSEEK_API_BASE is required; EMBEDDING_BASE_URL is required; RAG_VECTOR_DB_URL is required; RAG_RERANKER_BASE_URL is required`，进程退出 | HTTP 200，healthy |
| recruitment | `RuntimeError: REDIS_URL is required; DEEPSEEK_API_BASE is required`，进程退出 | HTTP 200，healthy |
| data-query | `RuntimeError: REDIS_URL is required; DEEPSEEK_API_BASE is required`，进程退出 | HTTP 200，healthy |

### 未在本阶段验证的项

- 真实 DeepSeek API、生产 MySQL、飞书接入（按计划在 LEGAL-100 / RECRUIT-200 / DATA-300 / FEISHU-500 进行）
- LangGraph 业务节点（业务实现阶段）
- Playwright E2E、Lighthouse 性能预算（WEB-400）
- Alembic 真实 DB upgrade/downgrade（仅离线 ScriptDirectory 校验；真实 DB 需 MySQL 实例）
- 完整 `docker compose up` 多服务编排（compose 中 suite-web / suite-ops-nginx 仍注释，按计划在 WEB-410 / OPS-620 解除）
- Git 提交（按规范「未获得用户授权不执行 Git 提交或推送」，所有改动停留在工作区）
