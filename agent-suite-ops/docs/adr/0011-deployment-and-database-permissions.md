# ADR-0011：部署参数与数据库权限

- 状态：已确认
- 日期：2026-07-04
- 阶段：DESIGN-002

## 背景

五模块单仓架构需要在编码前固化端口分配、数据库账号模型、镜像版本、可观测约定，避免后期配置漂移。

## 决策

### 端口分配

| 服务 | 端口 |
|---|---|
| legal-consulting-agent | 8101 |
| recruitment-assistant-agent | 8102 |
| data-query-agent | 8103 |
| agent-suite-web (Vite dev) | 5173 |
| MySQL | 3306 |
| Redis | 6379 |
| Nginx (统一入口) | 80 / 443 |

端口分配通过环境模板注入，不得在代码中硬编码。

### 数据库 schema 与账号

- `legal_agent_db`：法律 Agent 读写账号；包含用户镜像、会话、知识库元数据、Prompt 版本、审计等。
- `recruitment_agent_db`：招聘 Agent 读写账号；包含任务、材料元数据、结构化结果、报告、审计等。
- `data_query_agent_db`：智能问数 Agent 读写账号；包含会话、SQL 审计、Prompt 版本等运行态数据。
- `shop_db`：智能问数 Agent **只读账号**，独立账号隔离，仅 `SELECT` 权限。

跨 schema 访问禁止；同 MySQL 实例多 schema 通过账号权限隔离。

### 版本矩阵

| 组件 | 版本 |
|---|---|
| Python | 3.12-slim |
| Node | 20-alpine |
| MySQL | 8.0.36 LTS |
| Redis | 7.4-alpine |
| Nginx | 1.27-alpine |
| FastAPI | 最新稳定 0.1xx |
| LangGraph | 最新稳定 0.2xx |
| SQLAlchemy | 2.x |
| Alembic | 1.13+ |
| Vue | 3.4+ |
| Vite | 5.x |
| Element Plus | 最新稳定 |
| Pydantic | 2.x |

具体锁定版本在 FOUND-010 第 1 步固化到 `pyproject.toml` / `package.json`。

### 字符集与时区

- 数据库：`utf8mb4` + `utf8mb4_unicode_ci`。
- 容器：`TZ=Asia/Shanghai`。
- 数据库存储 UTC，应用层转换展示。

### Redis 用途

- 登录限流（登录失败计数）。
- API 速率限制（用户级 token bucket）。
- SSE 心跳与断线检测。
- 短期缓存（Embedding 结果、SQL 结果摘要）。
- 不存储业务持久化数据。

### DeepSeek 调用

- 服务直连官方 API（不经代理网关）。
- 超时 60 秒，重试 3 次，指数退避（1s / 2s / 4s）。
- 独立 adapter，核心逻辑可在不访问真实 DeepSeek 的条件下单元测试。

### 反向代理

- Nginx 路由：
  - `/` → `agent-suite-web`
  - `/api/legal` → `legal-consulting-agent:8101`
  - `/api/recruitment` → `recruitment-assistant-agent:8102`
  - `/api/data` → `data-query-agent:8103`
- 所有路由支持 SSE 长连接（关闭 buffer，启用 `X-Accel-Buffering: no`）。

### Docker 安全

- 非 root 用户运行（每镜像创建 `app` 用户）。
- 多阶段构建，最终镜像仅包含运行时依赖。
- 每镜像内置 `HEALTHCHECK`。
- 镜像扫描（Trivy）在 CI 中执行，CRITICAL 漏洞阻断发布。

### 可观测约定

- 结构化 JSON 日志（Python `loguru` / Node `pino`）。
- 关联字段：`request_id`、`thread_id`、`run_id`、`node_name`、`error_code`、`user_id`（脱敏后）。
- 不记录：完整 Prompt、密钥、Token、简历原文、法律咨询原文、SQL 完整结果。

### 环境模板

- 每仓根目录 `.env.example`，仅占位值与说明。
- 真实密钥通过 Docker secret 或外部环境变量注入，不进入 Git。
- 启动时校验关键配置存在与范围；缺失快速失败。

## 后果

- Redis 成为运行依赖（限流、SSE 心跳）；移除需要降级方案。
- Nginx 必须正确配置 SSE，否则流式功能异常。
- 镜像版本固定便于追踪，但需要定期人工升级。

## 关键实现约束

- 所有端口、版本、超时、阈值通过类型化 Settings 或 `pyproject.toml` / `package.json` 管理。
- `.env.example` 必须与 Settings 字段一一对应。
- 部署文档以 `agent-suite-ops/docs/runbooks/deployment-topology.md` 为真源。

## 回滚

- 若 Redis 资源紧张，可移除 Redis，会话与限流改用数据库表（性能下降）。
- 若 Nginx 配置复杂度过高，首期可直连各 Agent API，前端通过环境变量切换 API 基址，不经过统一入口。
