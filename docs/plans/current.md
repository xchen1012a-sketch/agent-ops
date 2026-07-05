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

## 并行阶段：RECRUIT-200 智能招聘 Agent

- 由 Claude 推进；Codex 仍在 `LEGAL-100`，互不阻塞。
- 阶段文件：`docs/plans/phases/RECRUIT-200-recruitment-assistant-agent.md`。
- 子阶段：`RECRUIT-230` 数据层（7 批）→ `RECRUIT-240` 工作流（10 切片）→ `RECRUIT-250` API/报告（5 切片）→ `RECRUIT-260` 质量验收（4 切片）。
- 当前状态：`RECRUIT-250` 第五切片报告生成/查看/导出 API 与 `RECRUIT-260` 课程 MVP 质量验收收尾已完成并通过门禁（ruff/mypy/pytest 86%/214 passed/单 head `hhh5c9e3f660`）；招聘模块本地 mock 闭环已可用于全栈对接，真实 DeepSeek/ClamAV/Redis/MySQL/PDF 引擎后置。
