# data-query-agent

基于 LangGraph、FastAPI、MySQL 和 DeepSeek `deepseek-chat` 的独立智能问数 Agent API，同时为统一 Web 和飞书机器人提供能力。

当前阶段已完成 FOUND-010 工程基线，包含最小 FastAPI/LangGraph 应用壳、健康检查、迁移基线、测试基座和 Dockerfile；NL2SQL、SQL 安全执行和飞书适配等待 DATA-300/FEISHU-500 授权。

## Status

- Phase: FOUND-010（工程基线完成，等待 DATA-300 授权）
- Real source: `docs/specification.md`、`docs/detailed-design.md`
- Decisions: `agent-suite-ops/docs/adr/0007-unified-auth.md`、`0010-data-query-sql-safety.md`、`0011-deployment-and-database-permissions.md`

## 验证状态（FOUND-010）

工程基线（端口 8103）：

- [x] Ruff check + format 全绿（0 errors）
- [x] MyPy strict 全绿
- [x] Pytest 覆盖率 84%（>= 80% 阈值）
- [x] Alembic 基线迁移 `0001_initial_baseline` 单一 head
- [x] Docker 镜像构建 + 独立运行成功（python:3.12-slim，非 root UID 1001，tini PID 1，HEALTHCHECK 路径 `/v1/health/live`，docker inspect `State.Health.Status = healthy`）
- [x] `.env.example` 仅占位值；启动校验 `JWT_SECRET >= 32 bytes`、`REDIS_URL`、`DEEPSEEK_API_BASE` 等关键配置；缺失时 `lifespan` 抛 `RuntimeError` 进程退出
- [x] pip-audit（OSV）：asyncmy + chromadb + ecdsa 共 3 类漏洞

未验证 / 待后续阶段：

- [ ] NL2SQL + SQL 安全校验（DATA-300）
- [ ] 飞书机器人适配（FEISHU-500）

### 已知漏洞与处理

| 漏洞 | 来源 | 处理 |
|---|---|---|
| asyncmy 0.2.11 (PYSEC-2026-286) | 直接依赖 | 上游无 fix；只读 MySQL 账号缓解（ADR-0010/0011），监控上游 |
| chromadb 1.5.9 (PYSEC-2026-311) | 直接依赖（向量库） | 上游无 fix；内部使用不暴露公网 |
| ecdsa 0.19.2 (CVE-2024-23342) | python-jose 间接依赖 | 当前未实际调用 JWT；DATA-300 评估切换 PyJWT 或限制算法 |
