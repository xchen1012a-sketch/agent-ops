# 当前阶段

- 阶段：`LEGAL-100`
- 名称：法律咨询 Agent 业务实现
- 状态：`LEGAL-150 领域 API 与课件功能` 第五切片已落地：高风险审核入队 API 契约
- 阶段文件：`docs/plans/phases/LEGAL-100-legal-consulting-agent.md`
- 最近修复：
  - `REV-legal-data-integrity` 已完成第一阶段。
  - 计划与验证证据：`docs/plans/phases/REV-legal-data-integrity.md`。
  - 已补齐咨询记录、未来表约束、路径语义和报告投影设计。
  - AgentRun 创建前已校验会话属于指定用户。
- 上一阶段：`FOUND-010 企业级工程基础`
  - 状态：已完成
  - 本地提交：`9286bdd feat(foundation): complete enterprise baseline`
  - Docker 健康检查路径后由 `76556f5` 修正为 `/v1/health/live`。
- 当前执行入口：
  - 模块：`agents/legal-consulting-agent`
  - 已实现对象：`users`、`legal_categories`、`sessions`、`messages`、`agent_runs`、`node_runs`、`consultation_records`、`feedbacks`、`high_risk_reviews`、`prompt_versions`、`knowledge_materials`
  - 已实现工作流边界：`LegalWorkflowState`、`input_safety`、`classification`、`context_build`、`retrieval`、`generation`、`citation_check`、`risk_check`、`persist`、`build_legal_workflow_graph`
  - 已实现审计边界：`LegalWorkflowAuditService`、`map_workflow_error`、节点 started/finished 记录、retryable 错误到 `RunStatus.RETRYING` 映射
  - 已实现 runner 边界：`LegalWorkflowRunnerService`、`WorkflowNodeSpec`、`WorkflowRunResult`、`prepare_retry_state`、`mark_canceled`
  - 已实现 Prompt 边界：`PromptTemplateLoader`、`PromptRenderResult`、`validate_template_key`、`extract_required_variables`、`PromptOutputValidator`、`parse_json_object_output`
  - 已实现 Prompt-backed classification 边界：`LegalClassificationPromptService`、`TextLLMAdapter`、`make_prompt_classification_node`、graph classification handler 注入
  - 已实现 Prompt-backed generation 边界：`LegalGenerationPromptService`、`LegalGenerationResult`、`make_prompt_generation_node`、graph generation handler 注入
  - 已实现 Prompt-backed risk_check 边界：`LegalRiskCheckPromptService`、`LegalRiskCheckResult`、`make_prompt_risk_check_node`、graph risk_check handler 注入
  - 已实现 prompt-backed workflow 装配边界：`LegalPromptWorkflowFactory`、`LegalPromptWorkflowPrompts`
  - 已实现 LEGAL-150 会话创建 API：`POST /v1/sessions`、`POST /api/legal/v1/sessions`、会话 DTO、trusted user public id 请求边界
  - 已实现 LEGAL-150 问答入口 API：`POST /v1/sessions/{session_public_id}/questions`、`LegalQuestionAnswerService`、问答 DTO
  - 已实现 LEGAL-150 历史消息查询 API：`GET /v1/sessions/{session_public_id}/messages`、消息分页 DTO、repository 只读查询
  - 已实现 LEGAL-150 反馈 API：`POST /v1/sessions/{session_public_id}/messages/{message_public_id}/feedback`
  - 已实现 LEGAL-150 高风险审核入队 API：`POST /v1/sessions/{session_public_id}/messages/{message_public_id}/high-risk-review`
- 暂不具备 / 后置依赖：
  - 课件法律知识库样本未提供；第一切片仅实现 mock/adapter 边界。
  - 知识材料导入、Qdrant 索引、BGE embedding/reranker、真实 RAG 检索和 DeepSeek 真实问答仍未开始。
- 下一步：
  - 继续 `LEGAL-150` 第六切片：报告导出 API 契约，基于咨询记录生成同步 Markdown 投影。
  - 知识材料导入、切分、向量索引、检索和真实 DeepSeek 调用等待知识库样本与本地服务边界确认。

## 并行阶段：RECRUIT-200 智能招聘 Agent

- 由 Claude 推进；Codex 仍在 `LEGAL-100`，互不阻塞。
- 阶段文件：`docs/plans/phases/RECRUIT-200-recruitment-assistant-agent.md`。
- 子阶段：`RECRUIT-230` 数据层（7 批）→ `RECRUIT-240` 工作流（10 切片）→ `RECRUIT-250` API/报告（5 切片）→ `RECRUIT-260` 质量验收（4 切片）。
- 当前状态：`RECRUIT-230` 第一批（身份与任务材料层 5 张表）已落地并通过质量门禁（ruff/mypy/pytest 82%/40 passed/单 head）。下一步进入第二批：简历结构化层。
