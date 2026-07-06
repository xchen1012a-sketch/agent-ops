# 三 Agent 知识文件与 MVP 完成计划书

> 状态：计划书已按当前 `docs/homework/` 资料刷新，并已拆分为 `KNOW-000` 到 `KNOW-400` 阶段执行。
> 原则：只写当前仓库、课程资料和本地运行证据能证明的内容；真实 Dify、飞书、DeepSeek、外部 MySQL 没有联调证据时，一律按“本地等价/演示模式”描述。

## 1. 目标

基于当前项目和 `docs/homework/` 课程资料，把法律助手、招聘助手、问数助手收敛成可运行、可演示、可写报告的 MVP。

MVP 完成标准：

- 三个 Agent 都能从统一侧边栏进入，使用 Claude 风格对话体验，不保留复杂后台子菜单。
- 最近对话统一放在侧边栏保存和展示。
- 每个 Agent 都有明确的知识文件或规则来源、运行链路、测试或 smoke 证据。
- 报告只声明已验证内容，不把本地 mock/fixture 写成真实外部服务联调。

## 2. 当前可用资料

| 类型 | 路径 | 用途 |
| --- | --- | --- |
| 实训报告大纲 | `docs/homework/实训报告大纲.html` | 规定三章交付：法律咨询、Dify 工作流智能体、智能问数 |
| 报告模板 | `docs/homework/2025-2026-2《大数据应用实训》实训报告 姓名.docx` | 最终报告格式来源 |
| 法律课程 | `docs/homework/AI编程_智能问数实训(课件)/03_AI法律咨询系统实战/` | 法律咨询系统课程目标、功能和页面参考 |
| Dify 节点案例 | `docs/homework/AI编程_智能问数实训(课件)/05_Dify工作流智能体开发/dify案例实战/` | 招聘助手可映射为参数提取、条件分支、代码执行、模板输出等工作流节点 |
| 智能问数课程 | `docs/homework/AI编程_智能问数实训(课件)/06_智能问数/` | 数据字典、架构、宽表、NL2SQL Prompt、端到端案例 |
| shop_db SQL | `docs/homework/AI编程_智能问数实训(课件)/shop_db_export.sql` | 问数系统课程数据来源，可作为后续真实 MySQL 导入材料 |
| 飞书到 Dify 示例 | `docs/homework/AI编程_智能问数实训(课件)/feishu-to-dify/` | 飞书接入参考代码；当前不读取或引用 `.env` 密钥 |

## 3. 三个 Agent 的知识与配置要求

| Agent | 需要的知识文件 | 还需要的配置/规则 | MVP 完成效果 |
| --- | --- | --- | --- |
| 法律助手 | 法律课程资料 + 项目内最小法律知识 seed | 分类、风险提示、建议结构、来源状态、免责声明 | 用户提问后返回结构化法律咨询建议，保存最近咨询。当前不声明完整法规库。 |
| 招聘助手 | Dify 节点案例 + 项目内招聘规则 JSON | 简历/JD 字段抽取、匹配评分、公平性敏感字段过滤、报告模板 | 用户在对话中输入 JD 和简历，返回匹配分、证据、风险点、面试问题。当前不需要 RAG 候选人库。 |
| 问数助手 | 智能问数课件、`shop_db_export.sql`、宽表/NL2SQL Prompt、项目内 schema/fixture | SQL 白名单、AST 安全策略、本地只读查询适配器、图表语义、飞书 mock 入口 | 用户用自然语言问数，系统展示 SQL、结果表、解释和图表。当前以本地 deterministic fixture 验证，不声明真实 MySQL/飞书联调。 |

## 4. 阶段计划与执行状态

| 阶段 | 文件 | 目标 | 状态 |
| --- | --- | --- | --- |
| KNOW-000 | `docs/plans/phases/KNOW-000-source-inventory.md` | 固定知识源、完成标准、缺口和不得虚构边界 | 已完成，后续按当前课件目录刷新边界 |
| KNOW-100 | `docs/plans/phases/KNOW-100-legal-knowledge-assistant.md` | 法律助手最小知识包与法律问答链路 | 已完成后端最小 seed 和测试验证 |
| KNOW-200 | `docs/plans/phases/KNOW-200-recruitment-conversation-workflow.md` | 招聘助手对话化、规则化、工作流证据 | 已完成规则包、分析结果、报告和前端展示 |
| KNOW-300 | `docs/plans/phases/KNOW-300-data-query-knowledge-sql.md` | 问数知识文件、SQL 安全、结果和图表证据 | 已完成 local-demo API、Web 展示、飞书 mock 语义和测试 |
| KNOW-400 | `docs/plans/phases/KNOW-400-demo-report-acceptance.md` | MVP 运行证据、验收边界、最终报告素材 | 当前收口阶段 |

## 5. 不做事项

- 不把未验证的真实 Dify 应用写成已部署。
- 不把未联调的飞书租户、企业微信、DeepSeek、外部 MySQL 写成已完成。
- 不把法律助手写成完整法规全文库。
- 不恢复复杂后台菜单；MVP 以对话入口、最近对话和报告证据为主。
- 不为招聘助手先做候选人库或 RAG，除非后续明确要求扩展。

## 6. 当前收口口径

本项目不是生产项目，当前目标是课程 MVP 达标：本地能跑、核心链路能演示、报告材料能说明实现方式和边界。后续如果需要真实部署，再单独进入外部服务联调阶段。
