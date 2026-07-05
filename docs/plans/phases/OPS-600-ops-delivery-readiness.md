# OPS-600 运维与本地集成准备

## 状态

- 状态：准备阶段已建立；等待前端、智能问数、招聘 Agent 当前并行开发收口后执行完整联调。
- 当前不修改前端、智能问数、招聘 Agent 业务代码。
- 本阶段先固化运维验收范围、统一启动/检查策略、服务依赖矩阵和失败降级口径。

## 目标

在不阻塞三个并行 AI 的前提下，为最终集成准备可复用的运维检查清单，确保后续能验证：

1. 三个 Agent、统一前端、MySQL、Redis、Qdrant/BGE、Nginx 的本地编排。
2. 服务健康检查、网关路由、环境变量和最小权限。
3. 单服务失败不影响其它业务菜单。
4. 不把真实 Secret、生产数据或外部服务默认接入本地验收。

## 范围

- `agent-suite-ops/docker-compose.yml` 的服务清单与现有 ADR/Runbook 对齐检查。
- `agent-suite-ops/.env.example` 的变量完整性检查。
- Nginx 路由和三个 Agent 健康检查路径检查。
- 本地集成执行顺序、失败排查和回滚说明。
- 与 QA-700 的质量门禁衔接。

## 不做事项

- 不改 `agent-suite-web/`。
- 不改 `agents/data-query-agent/`。
- 不改 `agents/recruitment-assistant-agent/`。
- 不连接真实 DeepSeek、真实飞书租户、生产 MySQL 或生产 Redis。
- 不自动启动长期后台服务。
- 不自动提交或推送 Git。

## 服务依赖矩阵

| 服务 | 依赖 | 健康检查 | 当前集成策略 |
|---|---|---|---|
| `legal-agent` | MySQL、Redis；真实 RAG/DeepSeek 后置 | `/health/live`、`/health/ready` | 法律模块本地质量门禁已通过；Docker/E2E 后置 |
| `recruitment-agent` | MySQL、Redis；ClamAV/DeepSeek 后置 | `/health/live`、`/health/ready` | 等 RECRUIT-240/250/260 收口 |
| `data-query-agent` | MySQL、Redis、`shop_db` 只读；MCP/DeepSeek/飞书后置 | `/health/live`、`/health/ready` | 等 DATA-300 循环完成 |
| `suite-web` | 三 Agent 公开 API/SSE | `/health/live` | 等 WEB-400 业务页收口 |
| `suite-ops-nginx` | web + 三 Agent | nginx status / route smoke | 在 API prefix 冻结后验证 |
| `mysql` | 无 | `mysqladmin ping` | 本地 dev 数据，不接生产 |
| `redis` | 无 | `redis-cli ping` | 本地限流/SSE/cache |
| `qdrant` / BGE | 法律 RAG | `/healthz` / `/health` | 未提供知识样本前只做服务可用性 |

## 执行步骤草案

### OPS-610：运维文档冻结

- 核对 ADR-0011、deployment-design、docker-compose、`.env.example`。
- 输出变量缺口和路由缺口。
- 不启动服务。

### OPS-620：单模块容器检查

- 分别构建或检查 legal / recruitment / data-query / web 镜像。
- 每个模块只跑自身 health smoke。
- 未完成模块只记录未验证。

### OPS-630：本地依赖启动

- 启动 MySQL、Redis、Qdrant/BGE 等本地依赖。
- 验证端口、健康状态、数据卷、权限模型。
- 不导入真实数据。

### OPS-640：统一网关联调

- 验证 `/api/legal/v1`、`/api/recruitment/v1`、`/api/data/v1` 和前端静态资源路由。
- 验证任一 Agent 下线时其它模块仍可用。

### OPS-650：排障与回滚

- 整理日志字段、request_id / run_id 关联、常见错误码。
- 记录 stop / cleanup / rollback 步骤。

## 验收证据模板

| 验证项 | 命令/步骤 | 期望 | 实际 | 状态 |
|---|---|---|---|---|
| Compose 配置解析 | `docker compose config` | 无语法错误 | 待执行 | 未验证 |
| MySQL health | `docker compose ps mysql` | healthy | 待执行 | 未验证 |
| Redis health | `docker compose ps redis` | healthy | 待执行 | 未验证 |
| Legal health | `GET /api/legal/v1/health/live` | 200 | 待执行 | 未验证 |
| Recruitment health | `GET /api/recruitment/v1/health/live` | 200 | 待执行 | 未验证 |
| Data health | `GET /api/data/v1/health/live` | 200 | 待执行 | 未验证 |
| Web health | `GET /health/live` | 200 | 待执行 | 未验证 |
| Gateway fallback | stop one Agent | other routes still available | 待执行 | 未验证 |

## 当前已知未验证项

- Docker Compose 全量启动未验证。
- Nginx 统一入口未验证。
- 数据库账号最小权限未用真实 MySQL 复验。
- Qdrant/BGE/RAG 真实链路未验证。
- 飞书真实租户未验证。

## 停止条件

- 需要真实生产 Secret、真实生产数据库或真实用户数据。
- 需要终止未知进程或占用端口进程。
- 未完成模块要求改变公开 API/DB/权限边界。
- Docker 编排需要业务模块互相 import 或共享业务库。

## 回滚方式

- 文档阶段：删除或修订本阶段文档，不影响业务模块。
- Compose 阶段：停止本地 compose stack，保留数据卷前先导出；不得删除用户数据。
- 网关阶段：回退到各服务直连端口验证。
