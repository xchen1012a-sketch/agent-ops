# 本地 Agent 依赖与环境 Runbook

本文只覆盖三个 Agent 的本地依赖、环境变量、启动和健康检查，不覆盖 API 配置中心的业务实现。

## 结论

运行方式采用“共享基础设施 + Agent 独立 runtime”：

- 共享：Docker、MySQL、Redis，法律 RAG 需要时再共享 Qdrant、BGE embedding、BGE reranker。
- 独享：三个 Agent 各自的 Python `.venv`、`.env`、端口、业务 schema、迁移账号和运行账号。
- 用户 API key：由系统 API 配置中心按账号保存，不能写入共享 `.env`。
- 系统 secret：`JWT_SECRET`、`AGENT_CONFIG_ENCRYPTION_KEY`、数据库密码属于部署环境配置，不属于用户 API key。
- 本机 3306/6379 已被占用时，`agent-suite-ops/docker-compose.local.yml` 将项目 MySQL/Redis 映射到 13306/16379。

## 当前依赖审查

| Agent | 端口 | Python runtime | 最小基础设施 | 真业务额外依赖 |
|---|---:|---|---|---|
| legal | 8101 | 独立 `.venv` | MySQL、Redis、模块 `.env` | DeepSeek、Qdrant、BGE embedding、BGE reranker、法律知识库 |
| recruitment | 8102 | 独立 `.venv` | MySQL、Redis、模块 `.env` | DeepSeek；OCR 仅用于扫描简历/JD，文本/PDF 文本可不依赖 OCR |
| data | 8103 | 独立 `.venv` | MySQL、Redis、`shop_db` 只读连接、模块 `.env` | DeepSeek、MCP/只读查询链路；飞书是入口能力，可选 |

## 最小启动层级

1. 进程可启动：`.env` 通过启动校验，数据库引擎能初始化，`/v1/health/live` 返回 200。
2. 依赖可用：数据库迁移完成，Redis/MySQL 可连，`/v1/health/ready` 返回 200。
3. 真业务可用：用户在系统 API 配置页填入自己的 DeepSeek/API key；法律 RAG、问数执行、招聘真匹配所需外部依赖就绪。

## 脚本

检查环境：

```powershell
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\check-agent-env.ps1 -Agent all
```

启动本地依赖与 Agent：

```powershell
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\start-agent-runtime.ps1 -Agent all
```

首次初始化或迁移本地数据库时：

```powershell
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\start-agent-runtime.ps1 -Agent all -Migrate
```

法律 RAG 依赖较重，只有需要验证法律 RAG 时再启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\start-agent-runtime.ps1 -Agent legal -WithLegalRag
```

健康检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\smoke-agent-health.ps1 -Agent all
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\smoke-agent-health.ps1 -Agent all -RequireReady
```

停止由脚本启动的本地 Agent 进程：

```powershell
powershell -ExecutionPolicy Bypass -File .\agent-suite-ops\scripts\stop-agent-runtime.ps1 -Agent all
```

## 环境变量边界

三个 Agent 的模块 `.env` 需要保留系统运行配置：

- `JWT_SECRET`
- `DATABASE_URL`
- `DATABASE_MIGRATION_URL`
- `REDIS_URL`
- `AGENT_CONFIG_ENCRYPTION_KEY`
- data 额外需要 `SHOP_DB_READ_URL`
- legal 额外需要 `EMBEDDING_BASE_URL`、`RAG_VECTOR_DB_URL`、`RAG_RERANKER_BASE_URL`

DeepSeek、OCR、MCP、飞书这类用户可配置的外部 API key 应进入系统 API 配置中心，并按账号隔离。当前 API 接入未完成前，如果启动校验仍要求 `DEEPSEEK_API_KEY`，只能作为临时兼容项处理，不作为长期环境设计。

## 稳定运行建议

- 开发调试使用本地 `.venv` + `start-agent-runtime.ps1`，便于看日志和快速重启。
- 联调和演示使用 `agent-suite-ops/docker-compose.yml`，由 Compose 管理 MySQL、Redis、Qdrant、BGE 和三个 Agent。
- MySQL 继续保持 4 个 schema 独立账号；`shop_db` 只读账号只给 data-query 使用。
- 不把用户 API key 放进 `agent-suite-ops/.env` 或三个模块 `.env`。
- 健康检查分层：`live` 判断进程，`ready` 判断运行依赖，业务 smoke 判断真实 LLM/RAG/问数链路。
