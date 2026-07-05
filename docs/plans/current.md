# Current Phase

- Phase: `DATA-300`
- Name: Data Query Agent full-module loop development
- Status: Completed local planned scope through DATA-390 loop 32.
- Phase file: `docs/plans/phases/DATA-300-data-query-agent.md`
- Current module: `agents/data-query-agent`
- Planned scope: data dictionary, runtime data layer, SQL safety policy, query execution adapter, LangGraph workflow, Prompt/LLM boundary, Web API/SSE, evaluation, Feishu adapter, final acceptance.
- Completed loops: DATA-310 through DATA-390 loops 1-32.
- Do not modify: legal Agent, recruitment Agent, other modules, or unrelated parallel AI changes.
- External services: real DeepSeek, real MySQL, and real Feishu tenant remain intentionally unconnected in this local module scope.
- Next step: choose the next module/phase or explicitly start real external-service integration planning.

## 并行阶段：RECRUIT-200 智能招聘 Agent

- 由 Claude 推进；Codex 仍在 `LEGAL-100`，互不阻塞。
- 阶段文件：`docs/plans/phases/RECRUIT-200-recruitment-assistant-agent.md`。
- 子阶段：`RECRUIT-230` 数据层（7 批）→ `RECRUIT-240` 工作流（10 切片）→ `RECRUIT-250` API/报告（5 切片）→ `RECRUIT-260` 质量验收（4 切片）。
- 当前状态：`RECRUIT-240` 第六切片 Prompt-backed `resume_parse` 节点已落地并通过质量门禁（ruff/mypy/pytest 83%/186 passed/单 head `hhh5c9e3f660`）；下一步按课程项目节奏合并推进剩余 Prompt 节点闭环：`jd_parse` / `evidence_match` / `fairness_check` / `gap_question_gen` / workflow assembly。
