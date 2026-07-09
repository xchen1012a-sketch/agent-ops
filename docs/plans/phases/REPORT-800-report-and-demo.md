# REPORT-800 实训报告与演示材料准备

## 状态

- 状态：报告与演示骨架已建立；等待各模块最终验收证据和截图补齐。
- 当前可写架构、分包策略、法律 Agent 证据、风险与未验证项。
- 前端、智能问数、招聘的最终功能截图需等并行任务完成后补充。

## 目标

形成可提交、可答辩、可追溯的实训交付材料：

1. 项目实训报告。
2. 架构图与模块边界说明。
3. 三个 Agent 的实现说明和测试证据。
4. 前端演示流程和截图。
5. 运维部署说明。
6. 风险、未验证项和后续优化。

## 报告建议目录

```text
1. 项目背景与目标
2. 总体架构设计
   2.1 单仓多模块策略
   2.2 统一前端 + 三 Agent + 运维协调
   2.3 API / SSE / 数据库 / 外部服务边界
3. 关键技术选型
   3.1 FastAPI + Pydantic v2
   3.2 LangGraph 工作流
   3.3 SQLAlchemy 2 + Alembic
   3.4 Vue 3 + Element Plus
   3.5 DeepSeek / RAG / SQL 安全 / 飞书适配
4. 法律咨询 Agent 实现
   4.1 数据层
   4.2 工作流
   4.3 API 与 SSE
   4.4 测试与验收证据
5. 智能招聘 Agent 实现
   5.1 材料结构化
   5.2 匹配与公平性
   5.3 API / 报告 / 人工复核
   5.4 测试与验收证据
6. 智能问数 Agent 实现
   6.1 数据字典与指标真源
   6.2 NL2SQL 与 SQL 安全
   6.3 查询执行、审计和图表语义
   6.4 飞书 mock / 接入边界
7. 统一 Web 前端
   7.1 页面结构
   7.2 API/SSE client
   7.3 降级与错误状态
8. 运维部署与安全
   8.1 Docker Compose / Nginx
   8.2 数据库权限
   8.3 日志与可观测
   8.4 Secret 外置
9. 测试与质量保障
10. 演示流程
11. 总结与后续优化
```

## 演示脚本草案

| 顺序 | 演示项 | 输入/动作 | 期望结果 | 证据 |
|---|---|---|---|---|
| 1 | 系统健康页 | 打开 Web 健康检查 | 三个 Agent 状态可见 | 截图待补 |
| 2 | 法律咨询 | 创建会话并提问 | 返回回答、引用/免责声明、SSE 事件 | 法律 API 已有本地测试；前端截图待补 |
| 3 | 法律历史与报告 | 查看历史、生成 Markdown 报告 | 可查看咨询记录和报告 | 截图待补 |
| 4 | 招聘分析 | 创建任务、上传材料/使用样例 | 结构化结果、匹配和面试问题 | 待 RECRUIT-250/260 |
| 5 | 招聘人工复核 | admin 审核报告 | 报告签字后输出 | 待 RECRUIT-250/260 |
| 6 | 智能问数 | 输入课件标准问题 | 返回表格/解释/图表语义 | 待 DATA-300 |
| 7 | SQL 安全 | 输入危险 SQL/越权问题 | 被策略拦截并审计 | 待 DATA-300 安全集 |
| 8 | 服务降级 | 停止一个 Agent | 其它菜单仍可用，故障菜单显示降级 | 待 OPS-600/QA-700 |

## 当前可用证据

### 法律 Agent

| 证据 | 状态 |
|---|---|
| Ruff lint | 通过 |
| Format check | 通过 |
| MyPy | 通过 |
| Pytest | `133 passed` |
| Coverage | `90%` |
| Alembic heads | single head `ceeb31ed5ac6` |
| OpenAPI smoke | `28` paths |

### 架构与计划

| 证据 | 文件 |
|---|---|
| 总体计划 | `docs/plans/project-plan.md` |
| 当前阶段入口 | `docs/plans/current.md` |
| ADR | `agent-suite-ops/docs/adr/` |
| 运维设计 | `agent-suite-ops/docs/runbooks/deployment-design.md` |
| 法律封版说明 | `agents/legal-consulting-agent/docs/acceptance-closeout.md` |
| QA 验收矩阵 | `docs/plans/phases/QA-700-quality-acceptance.md` |

## 待补材料

| 材料 | 来源阶段 | 状态 |
|---|---|---|
| 前端页面截图 | WEB-400 | 待补 |
| 招聘 Agent 最终测试输出 | RECRUIT-260 | 待补 |
| 智能问数 8 题与安全攻击测试输出 | DATA-300 | 待补 |
| Docker Compose 启动截图/日志 | OPS-600 | 待补 |
| Nginx 统一入口截图 | OPS-600 | 待补 |
| E2E 测试结果 | QA-700 | 待补 |

## 答辩亮点

- 单仓多模块：统一管理、独立边界、便于 AI 并行开发。
- 三 Agent 隔离：不互相 import、不共享业务数据库、不跨模块调用私有接口。
- LangGraph 工作流：显式 state、节点、失败语义和审计。
- 智能问数 SQL 安全：AST、白名单、资源限制、只读账号和审计。
- 招聘公平性：敏感属性剔除、证据化匹配、人工复核。
- 法律合规：引用校验、高风险审核、免责声明。
- 工程质量：ruff/mypy/pytest/alembic/vue-tsc/eslint/build/compose 分层验收。

## 风险说明模板

报告中必须如实说明：

- 未接真实生产服务。
- 外部服务使用 fake/mock 或未验证时必须标注。
- 飞书真实租户接入在 FEISHU-500 或后续阶段。
- 法律 RAG 的真实知识库效果依赖样本质量和检索服务联调。
- 智能问数只读安全依赖数据库账号权限和 SQL 策略双重验证。
