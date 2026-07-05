# 当前阶段

- 阶段：`LEGAL-100`
- 名称：法律咨询 Agent 业务实现
- 状态：`LEGAL-130 身份与数据层` 第一批 6 张表已实现并通过本地验证
- 阶段文件：`docs/plans/phases/LEGAL-100-legal-consulting-agent.md`
- 上一阶段：`FOUND-010 企业级工程基础`
  - 状态：已完成
  - 本地提交：`9286bdd feat(foundation): complete enterprise baseline`
  - 验证证据：见 `docs/plans/phases/FOUND-010-enterprise-foundation.md`
- 用户确认的阶段决策（2026-07-05）：
  1. 切换到 `LEGAL-100`
  2. 第一块先做 `LEGAL-130 身份与数据层`
  3. RAG 和知识库索引放到 `LEGAL-140`
  4. 法律分类先只建表，不预置分类数据
- 当前执行入口：
  - 模块：`agents/legal-consulting-agent`
  - 第一批对象：`users`、`legal_categories`、`sessions`、`messages`、`agent_runs`、`node_runs`
- 暂不具备 / 后置依赖：
  - 课件法律知识库样本未提供；不阻塞 `LEGAL-130`
  - 知识材料导入、Qdrant 索引、BGE embedding/reranker、RAG 检索和 DeepSeek 真实问答放到 `LEGAL-140`
- 下一步：
  - 继续 `LEGAL-130` 后续表：`consultation_records`、`prompt_versions`、`feedbacks`、`reports` / `export_tasks`、`high_risk_reviews`
  - `knowledge_materials` 可先建元数据表，但导入、切分、向量索引和检索仍放到 `LEGAL-140`
