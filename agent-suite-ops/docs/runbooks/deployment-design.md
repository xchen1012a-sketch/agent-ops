# OPS-610 部署详细设计

> 状态：DESIGN-002 子阶段设计产出，待 FOUND-010 / OPS-620+ 编码实现。
> 真源：本文件 + `adr/0006-monorepo-boundary.md` + `adr/0011-deployment-and-database-permissions.md`。

## 1. 服务清单

| 服务名 | 模块 | 容器内端口 | 宿主机映射 | 健康检查 | 启动顺序 |
|---|---|---|---|---|---|
| `legal-agent` | `agents/legal-consulting-agent` | 8101 | 8101 | `/health/live` + `/health/ready` | 5 |
| `recruitment-agent` | `agents/recruitment-assistant-agent` | 8102 | 8102 | `/health/live` + `/health/ready` | 5 |
| `data-query-agent` | `agents/data-query-agent` | 8103 | 8103 | `/health/live` + `/health/ready` | 5 |
| `suite-web` | `agent-suite-web` | 80 (nginx 内置) | 5173 (dev) / 8080 (prod) | `/health/live` | 6 |
| `suite-ops-nginx` | `agent-suite-ops` | 80 / 443 | 80 / 443 | nginx built-in | 7 |
| `mysql` | 标准 MySQL 镜像 | 3306 | 3306 | `mysqladmin ping` | 1 |
| `redis` | 标准 Redis 镜像 | 6379 | 6379 | `redis-cli ping` | 1 |
| `bge-embedding` | HuggingFace TEI (BGE-M3 dense+sparse) | 8080 | 8080 | `/health` | 2 |
| `bge-reranker` | HuggingFace TEI (BGE-Reranker-v2-m3) | 8081 | 8081 | `/health` | 2 |
| `qdrant` | Qdrant 向量库 | 6333 (HTTP) / 6334 (gRPC) | 6333 / 6334 | `/healthz` | 3 |

启动顺序依赖：`mysql / redis → bge-embedding / bge-reranker / qdrant → 三个 agent → suite-web → suite-ops-nginx`。

## 2. 网络拓扑

三个独立 Docker 网络隔离：

- `suite-frontend-net`：`suite-ops-nginx` ↔ `suite-web`。
- `suite-backend-net`：`suite-ops-nginx` ↔ `legal-agent` / `recruitment-agent` / `data-query-agent`。
- `suite-data-net`：三个 Agent ↔ `mysql` / `redis` / `bge-embedding`。

`suite-web` 不直连 `mysql` / `redis`；`suite-ops-nginx` 跨 `suite-frontend-net` 与 `suite-backend-net`。

## 3. 卷映射

| 卷名 | 挂载点 | 用途 |
|---|---|---|
| `mysql_data` | `/var/lib/mysql` | 业务数据库持久化 |
| `redis_data` | `/data` | Redis 持久化（AOF） |
| `qdrant_data` | `/qdrant/storage` | Qdrant 向量索引与 payload 持久化 |
| `legal_kb_data` | `/app/data/legal_kb` | 法律知识库源文件（PDF / Markdown） |
| `prompts_data` (legal/recruit/data-query) | `/app/data/prompts` | 版本化 Prompt 文件 |
| `logs_data` | `/var/log/suite` | 结构化日志（仅 dev / staging） |

生产环境日志通过 stdout 收集，不挂载卷。

## 4. 环境变量字典

### 4.1 通用（所有 Agent）

| 变量 | 必填 | 示例 | 说明 |
|---|---|---|---|
| `APP_ENV` | 是 | `dev` / `staging` / `prod` | 环境标识 |
| `APP_PORT` | 是 | `8101` | 服务监听端口 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别，默认 `INFO` |
| `LOG_FORMAT` | 否 | `json` | 日志格式，生产强制 `json` |
| `JWT_SECRET` | 是 | (32+ 字节随机) | JWT 签名密钥，启动校验长度 |
| `JWT_ACCESS_TTL_SECONDS` | 否 | `900` | access token 有效期，默认 15 分钟 |
| `JWT_REFRESH_TTL_SECONDS` | 否 | `604800` | refresh token 有效期，默认 7 天 |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | 否 | `5` | 登录限流，默认 5/min/IP |
| `RATE_LIMIT_API_PER_MINUTE` | 否 | `60` | API 限流，默认 60/min/user |
| `REDIS_URL` | 是 | `redis://redis:6379/0` | Redis 连接串 |

### 4.2 数据库

每个 Agent 通过独立环境变量配置自己的 schema：

```text
DATABASE_URL=mysql+asyncmy://legal_agent:<SECRET>@mysql:3306/legal_agent_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_RECYCLE_SECONDS=3600
DATABASE_SLOW_QUERY_SECONDS=5
```

`data-query-agent` 额外：

```text
SHOP_DB_READ_URL=mysql+asyncmy://data_query_reader:<SECRET>@mysql:3306/shop_db
SHOP_DB_READ_ONLY=true
SQL_EXECUTION_TIMEOUT_SECONDS=10
SQL_MAX_ROWS=1000
SQL_MAX_FIELDS=50
SQL_MAX_BYTES=1048576
SQL_AUDIT_RETENTION_DAYS=90
```

### 4.3 DeepSeek

```text
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_API_KEY=<SECRET>
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT_SECONDS=60
DEEPSEEK_MAX_RETRIES=3
DEEPSEEK_BACKOFF_SECONDS=1,2,4
```

### 4.4 法律 Agent 专属（ADR-0012 混合检索）

```text
LEGAL_KB_PATH=/app/data/legal_kb
HIGH_RISK_KEYWORDS_PATH=/app/data/legal_kb/high-risk-keywords.yaml
EMBEDDING_BASE_URL=http://bge-embedding:8080
EMBEDDING_MODEL=BAAI/bge-m3
RAG_VECTOR_DB_URL=http://qdrant:6333
RAG_VECTOR_COLLECTION=legal_kb
RAG_DENSE_WEIGHT=0.7
RAG_SPARSE_WEIGHT=0.3
RAG_RECALL_TOP_N=20
RAG_RERANK_TOP_N=5
RAG_SIMILARITY_THRESHOLD=0.65
RAG_CATEGORY_FILTER_ENABLED=true
RAG_RERANKER_ENABLED=true
RAG_RERANKER_BASE_URL=http://bge-reranker:8081
RAG_RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

### 4.5 招聘 Agent 专属

```text
FILE_UPLOAD_MAX_BYTES=10485760
FILE_UPLOAD_MAX_PAGES=20
FILE_UPLOAD_TEXT_MAX_BYTES=51200
CLAMAV_HOST=clamav
CLAMAV_PORT=3310
SCORING_RULES_PATH=/app/data/prompts/recruit/scoring-rules.yaml
FAIRNESS_TEST_THRESHOLD=0.05
```

### 4.6 智能问数 Agent 专属

```text
MCP_SERVER_URL=http://mcp-server:8080
MCP_TIMEOUT_SECONDS=30
SQL_WHITELIST_PATH=/app/data/prompts/data-query/sql-whitelist.yaml
INDICATORS_PATH=/app/data/prompts/data-query/indicators.yaml
FEISHU_ENABLED=false
```

### 4.7 前端专属

```text
VITE_API_BASE_URL=http://localhost
VITE_API_LEGAL_PREFIX=/api/legal
VITE_API_RECRUITMENT_PREFIX=/api/recruitment
VITE_API_DATA_PREFIX=/api/data
VITE_SESS_TIMEOUT_MINUTES=30
```

## 5. 数据库账号权限矩阵

| 账号 | 数据库 | SELECT | INSERT | UPDATE | DELETE | DDL | DML(写) | 系统库 |
|---|---|---|---|---|---|---|---|---|
| `legal_agent` | `legal_agent_db` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| `legal_migration` | `legal_agent_db` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `recruitment_agent` | `recruitment_agent_db` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| `recruitment_migration` | `recruitment_agent_db` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `data_query_agent` | `data_query_agent_db` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| `data_query_migration` | `data_query_agent_db` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `data_query_reader` | `shop_db` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

`REVOKE` 系统库（`mysql`、`information_schema`、`performance_schema`、`sys`）的显式权限；只读账号默认拒绝。

## 6. 镜像兼容矩阵

| 组件 | 镜像 | 版本 | 备注 |
|---|---|---|---|
| Python base | `python` | `3.12-slim` | 所有 Agent |
| Node base | `node` | `20-alpine` | 前端 |
| MySQL | `mysql` | `8.0.36` | LTS |
| Redis | `redis` | `7.4-alpine` | |
| Nginx | `nginx` | `1.27-alpine` | 反向代理 |
| BGE-M3 | `bge-m3` | 自构建（基于 `python:3.12-slim` + `sentence-transformers`） | Embedding 服务 |
| ClamAV | `clamav/clamav` | `1.4` | 招聘文件扫描 |
| FastAPI | `pip` | `0.115+` | |
| LangGraph | `pip` | `0.2.40+` | |
| SQLAlchemy | `pip` | `2.0.30+` | |
| Alembic | `pip` | `1.13+` | |
| Pydantic | `pip` | `2.7+` | |
| Vue | `npm` | `3.4+` | |
| Vite | `npm` | `5.x` | |
| Element Plus | `npm` | 最新稳定 | |
| sqlglot | `pip` | `25.10+` | SQL AST 校验 |

精确锁定版本在各仓 `pyproject.toml` / `package.json` 的 FOUND-010 第 1 步固化。

## 7. 故障矩阵

| 故障 | 影响 | 降级策略 |
|---|---|---|
| DeepSeek API 不可用 | 三个 Agent 流式回答失败 | 返回 `503 AGENT_DEPENDENCY_TIMEOUT`，前端展示"AI 服务繁忙，请稍后再试"；其他菜单可用 |
| MySQL 不可用 | 法律 / 招聘 / 智能问数运行态写入失败 | 健康检查 `/health/ready` 返回 503；前端降级 |
| `shop_db` 不可用 | 智能问数查询失败 | 返回 `503`；其他 Agent 不受影响 |
| Redis 不可用 | 限流、SSE 心跳失效 | 限流降级为内存计数（单实例）或直接放行（多实例需 Redis）；SSE 心跳超时由客户端主动重连 |
| BGE-M3 不可用 | 法律 RAG 检索失败 | 法律 Agent 降级为"无知识库"模式，仅输出免责声明 + 一般性信息 |
| MCP server 不可用 | 智能问数无法执行查询 | 保留 NL2SQL 生成能力，关闭执行入口；返回 `503 MCP_UNAVAILABLE` |
| 飞书长连接断开 | 飞书消息延迟 | 不影响 Web 端 |
| ClamAV 不可用 | 招聘文件上传失败 | 暂时拒绝上传，提示"安全服务不可用" |

## 8. 资源限制

| 服务 | CPU limit | Memory limit | 备注 |
|---|---|---|---|
| `legal-agent` | 1.0 | 1G | |
| `recruitment-agent` | 1.0 | 1G | |
| `data-query-agent` | 1.0 | 1G | |
| `suite-web` | 0.5 | 512M | |
| `mysql` | 2.0 | 2G | |
| `redis` | 0.5 | 256M | |
| `bge-embedding` | 2.0 | 2G | BGE-M3 dense+sparse 推理，CPU |
| `bge-reranker` | 1.0 | 1G | BGE-Reranker-v2-m3 cross-encoder |
| `qdrant` | 1.0 | 1G | 向量库，payload 索引 |
| `clamav` | 1.0 | 1G | |

## 9. 启动校验

每个 Agent 启动时必须校验：

- `JWT_SECRET` 长度 ≥ 32 字节。
- `DATABASE_URL` 可连接。
- `REDIS_URL` 可连接。
- `DEEPSEEK_API_KEY` 非空且可触发一次最小调用（可选，避免生产故障）。
- 法律 Agent 额外：`LEGAL_KB_PATH` 存在且可读。
- 招聘 Agent 额外：`SCORING_RULES_PATH` 可解析。
- 智能问数额外：`SQL_WHITELIST_PATH` 可解析。

任一校验失败立即退出非零状态码，不进入服务就绪。

## 10. 验收

- 单服务 `docker compose up <service>` 启动，`/health/live` 返回 200。
- 全栈 `docker compose up` 启动，5 个模块 `ready` 全绿。
- 模拟 MySQL 故障：智能问数 ready 变红，其他不受影响。
- 模拟 DeepSeek 故障：三个 Agent 流式返回 503，UI 降级。
- `git-preflight.ps1` 通过：无真实密钥、无课件、无超大文件。
