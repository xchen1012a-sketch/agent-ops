# Current Phase

- Phase: `MVP-003-prune-hidden-features`
- Name: Prune hidden non-MVP features
- Status: completed.
- Phase file: `docs/plans/phases/MVP-003-prune-hidden-features.md`
- Current module: `agent-suite-web`, `legal-consulting-agent`, `data-query-agent`.
- Planned scope: remove hidden frontend pages/routes/API clients and safe backend admin endpoints that are not needed by retained MVP flows.
- Do not modify: real external-service credentials, global Claude/Codex configuration, database schemas, core audit persistence, Feishu evidence endpoint, API config, retained legal/recruitment/data flows.
- External services: real DeepSeek, Dify, MCP and Feishu remain intentionally unconnected in this first MVP shell phase.
- Next step: continue MVP route/browser smoke only if a new issue appears.

## 并行阶段：STREAM-100 思考展示式 LLM 流式对接

- 阶段文件：`docs/plans/phases/STREAM-100-thinking-sse-streaming.md`。
- 状态：STREAM-100 阶段1-4 全部完成（三 Agent 后端两层+thinking、前端三页接入）。
- 已完成：CONFIG-200 配置中心↔流式 adapter 打通（无 key 回退 fake）。A1(data-query)/A2(配置页生效来源列)/A3(legal)/A4(recruitment，含前端补身份头) 全部完成并通过门禁。三 Agent 均按账号读配置中心：填 enabled 的 DeepSeek key → 真实流式，否则回退 fake。
- 计划文件：`docs/plans/phases/CONFIG-200-live-api-config-bridge.md`。
- 待办（需 key）：真实 DeepSeek 端到端联调。独立 bug：recruitment fairness 节点 `_redact_sensitive_fields` 未定义（task_46e7bc78）。
- 范围：三个 Agent（data-query/legal/recruitment）后端 SSE 两层中间件 + thinking 通道，`agent-suite-web` 三个会话页接入统一思考组件；模型无关、字段可配。
- 推进顺序：阶段1 data-query 后端样板（假流式）→ 停 → 阶段2 前端共享组件+data 接入 → 停 → 阶段3 legal → 停 → 阶段4 recruitment → 停 → 阶段5 真实 DeepSeek（需 key）→ 阶段6 收敛。

## 并行阶段：RECRUIT-200 智能招聘 Agent

- 由 Claude 推进；Codex 仍在 `LEGAL-100`，互不阻塞。
- 阶段文件：`docs/plans/phases/RECRUIT-200-recruitment-assistant-agent.md`。
- 子阶段：`RECRUIT-230` 数据层（7 批）→ `RECRUIT-240` 工作流（10 切片）→ `RECRUIT-250` API/报告（5 切片）→ `RECRUIT-260` 质量验收（4 切片）。
- 当前状态：`RECRUIT-250` 第五切片报告生成/查看/导出 API 与 `RECRUIT-260` 课程 MVP 质量验收收尾已完成并通过门禁（ruff/mypy/pytest 86%/214 passed/单 head `hhh5c9e3f660`）；招聘模块本地 mock 闭环已可用于全栈对接，真实 DeepSeek/ClamAV/Redis/MySQL/PDF 引擎后置。
