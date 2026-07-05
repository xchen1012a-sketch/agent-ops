# recruitment-assistant-agent

基于 LangGraph、FastAPI、MySQL 和 DeepSeek `deepseek-chat` 的独立智能招聘 Agent API。

当前阶段已完成 FOUND-010 工程基线，包含最小 FastAPI/LangGraph 应用壳、健康检查、迁移基线、测试基座和 Dockerfile；招聘业务功能等待 RECRUIT-200 授权。

## Status

- Phase: FOUND-010（工程基线完成，等待 RECRUIT-200 授权）
- Real source: `docs/specification.md`、`docs/detailed-design.md`
- Decisions: `agent-suite-ops/docs/adr/0007-unified-auth.md`、`0009-recruitment-fairness.md`、`0011-deployment-and-database-permissions.md`

## 验证状态（FOUND-010）

工程基线（端口 8102）：

- [x] Ruff check + format 全绿（0 errors）
- [x] MyPy strict 全绿
- [x] Pytest 覆盖率 83%（>= 80% 阈值）
- [x] Alembic 基线迁移 `0001_initial_baseline` 单一 head
- [x] Docker 镜像构建 + 独立运行成功（python:3.12-slim，非 root UID 1001，tini PID 1，HEALTHCHECK 路径 `/v1/health/live`，docker inspect `State.Health.Status = healthy`）
- [x] `.env.example` 仅占位值；启动校验 `JWT_SECRET >= 32 bytes`、`REDIS_URL`、`DEEPSEEK_API_BASE` 等关键配置；缺失时 `lifespan` 抛 `RuntimeError` 进程退出
- [x] pip-audit（OSV）：与 legal-consulting-agent 同 2 项（asyncmy、ecdsa），处理策略相同

未验证 / 待后续阶段：

- [ ] 简历/JD 解析与公平性评估（RECRUIT-200/210）
- [ ] 20 份合成脱敏样本作为验收基线（待用户确认）
