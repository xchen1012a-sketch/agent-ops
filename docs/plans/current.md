# Current Phase

- Phase: `DATA-300`
- Name: Data Query Agent full-module loop development
- Status: Loop plan created; next step is DATA-310 loop 1, schema / indicator / SQL whitelist source skeleton.
- Phase file: `docs/plans/phases/DATA-300-data-query-agent.md`
- Current module: `agents/data-query-agent`
- Planned scope: data dictionary, runtime data layer, SQL safety policy, query execution adapter, LangGraph workflow, Prompt/LLM boundary, Web API/SSE, evaluation, Feishu adapter, final acceptance.
- First loop: DATA-310 / loop 1, schema / indicator / whitelist configuration skeleton.
- Do not modify: legal Agent, recruitment Agent, other modules, or unrelated parallel AI changes.
- External services: do not connect real DeepSeek, real MySQL, or real Feishu tenant before adapter/fake boundaries are implemented and fixtures are confirmed.
- Next step: continue from loop 1 in `DATA-300-data-query-agent.md` unless the user interrupts or a stop condition is triggered.

## 并行阶段：RECRUIT-200 智能招聘 Agent

- 由 Claude 推进；Codex 仍在 `LEGAL-100`，互不阻塞。
- 阶段文件：`docs/plans/phases/RECRUIT-200-recruitment-assistant-agent.md`。
- 子阶段：`RECRUIT-230` 数据层（7 批）→ `RECRUIT-240` 工作流（10 切片）→ `RECRUIT-250` API/报告（5 切片）→ `RECRUIT-260` 质量验收（4 切片）。
- 当前状态：`RECRUIT-230` 第二批（简历结构化层 4 张表）已落地并通过质量门禁（ruff/mypy/pytest 80%/54 passed/单 head `bbb7c5d2e110`）。下一步进入第三批：JD 结构化层。
