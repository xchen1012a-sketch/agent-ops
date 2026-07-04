# 企业级多智能体应用平台总体计划

## 1. 项目目标

依据《大数据应用实训》课件的三个业务模块，建设一个统一前端、三个独立 Agent API 和一个运维协调模块组成的单仓项目：

- 法律咨询 Agent：迁移课件中的 AI 法律咨询系统。
- 智能招聘 Agent：采用实训报告大纲允许的“智能招聘助手”综合案例。
- 智能问数 Agent：迁移课件中的 Dify NL2SQL 工作流，并保留飞书入口。

三个 Agent 均使用 LangGraph 编排、FastAPI 暴露 API、MySQL 持久化，并调用 DeepSeek 官方 `deepseek-chat`。统一前端使用 Vite、Vue 3 和 Element Plus。

## 2. 已确认约束

- 前后端彻底分离，独立开发和部署。
- 三个 Agent 互不调用，不共享业务代码和业务表。
- 所有工程模块使用根目录的单一 Git 仓库，模块仍保持独立运行、数据和部署边界。
- 总体计划和子阶段计划位于 `docs/plans/`，与工程文件一起版本化。
- 模块真源规格和接口契约随对应代码仓库版本化。
- 所有配置通过环境变量或配置模型注入，不硬编码地址、密钥、模型、数据库或业务枚举。
- 禁止在业务代码中硬编码配置、Prompt、指标口径、权限矩阵、SQL 白名单、跨仓协议字段或环境差异；遵守各开源框架官方结构、API 和生命周期规范。
- 所有仓库强制读取并遵守 `.ai-spec/.ai-rules/development-standards.md`，未通过质量门禁不得进入阶段验收。
- 本计划确认后先完成架构与文档，不编写业务代码。

## 3. 目录与模块边界

```text
agent/
├─ agents/
│  ├─ legal-consulting-agent/      # 独立业务模块
│  ├─ recruitment-assistant-agent/ # 独立业务模块
│  └─ data-query-agent/            # 独立业务模块
├─ agent-suite-web/                # 统一前端模块
├─ agent-suite-ops/                # 运维协调模块
└─ docs/plans/                     # 总体与阶段计划
```

| 仓库 | 职责 | 禁止事项 |
|---|---|---|
| `agent-suite-web` | 统一 Vue 3 前端、三个模块菜单、API 客户端与交互状态 | 不实现 Agent、SQL、模型调用或后端业务规则 |
| `agents/legal-consulting-agent` | 法律咨询工作流、会话、知识检索、咨询记录与报告 API | 不实现招聘或智能问数逻辑 |
| `agents/recruitment-assistant-agent` | 简历/JD 解析、人岗分析、面试问题与报告 API | 不作自动录用决策，不访问其他 Agent 数据 |
| `agents/data-query-agent` | NL2SQL、SQL 安全校验、只读查询、数据解读、图表语义与飞书适配接口 | 不执行写 SQL，不实现其他业务域 |
| `agent-suite-ops` | 跨仓 Docker Compose、反向代理、环境模板、部署与排障文档 | 不承载业务代码、总体计划或真实密钥 |

项目根目录是唯一 Git 仓库；子目录不建立嵌套 Git 仓库。

## 4. 总体技术架构

```text
Vue 3 + Element Plus
        |
        +-- /api/legal ------> legal-consulting-agent ------> legal_agent_db
        +-- /api/recruitment -> recruitment-assistant-agent -> recruitment_agent_db
        +-- /api/data --------> data-query-agent ------------> shop_db
                                      ^
                                      |
                                  飞书机器人

三个 Agent API -> DeepSeek 官方 deepseek-chat
运维协调仓库   -> Docker Compose / Gateway / Health Check
```

## 5. Agent 统一工程约束

- 编排：LangGraph；节点必须有明确输入、输出和失败语义。
- API：FastAPI + Pydantic v2；OpenAPI 作为前后端契约。
- 数据：MySQL 8；SQLAlchemy 2 + Alembic；每个服务独立账号和 schema 权限。
- 运行状态：至少支持 `pending`、`running`、`success`、`failed`、`retrying`、`canceled`。
- 模型：DeepSeek 官方 `deepseek-chat`；超时、重试和限流由配置控制。
- 流式：SSE；必须支持非流式最终结果接口。
- 可观测：统一 `request_id`、`thread_id`、`run_id`、`node_name`、`error_code`。
- 安全：不记录密钥、完整 Prompt、简历原文、法律咨询原文或数据库明细到普通日志。
- 测试：单元、集成、契约、Agent 轨迹评估和端到端测试分层执行。
- 规范：FastAPI、LangGraph、Pydantic v2、SQLAlchemy 2、Alembic、Vue 3 和 Element Plus 均按官方推荐方式使用，不修改依赖源码、不调用废弃 API、不自建重复框架。

## 6. 阶段计划

| 阶段 | 目标 | 主要验收 |
|---|---|---|
| `ARCH-001` | 建立初始模块边界、总体架构和真源文档 | 模块文档齐全、无业务代码；原多仓决策由 `ARCH-003` 取代 |
| `ARCH-003` | 将工程和计划迁移到单一 Git 仓库 | 根仓唯一、课件排除、`main`/`develop` 推送成功 |
| `DESIGN-002` | 逐模块对齐详细设计、数据模型和 API 契约 | 未决问题清零，三模块设计经用户确认 |
| `FOUND-010` | 建立公共工程标准和各仓最小可运行骨架 | 各服务独立启动、健康检查通过 |
| `LEGAL-100` | 实现法律咨询 Agent | 课件基础功能与扩展验收通过 |
| `RECRUIT-200` | 实现智能招聘 Agent | 简历/JD/匹配/面试报告链路通过 |
| `DATA-300` | 实现智能问数 Agent | 课件 8 题与安全用例通过 |
| `WEB-400` | 完成统一 Web 集成 | 三菜单、流式交互、异常态和响应式验收通过 |
| `FEISHU-500` | 接入飞书智能问数 | 消息、会话、流式卡片与错误回传通过 |
| `OPS-600` | 完成跨仓容器化和运维设计 | 独立部署与统一编排均通过 |
| `QA-700` | 完成生产级质量验证 | 安全、性能、回归、恢复和文档证据完整 |
| `REPORT-800` | 完成实训报告与演示材料 | 三模块可演示，课件原文与迁移说明可追溯 |

## 6.1 模块详细计划

- `docs/plans/modules/agent-suite-web.md`
- `docs/plans/modules/legal-consulting-agent.md`
- `docs/plans/modules/recruitment-assistant-agent.md`
- `docs/plans/modules/data-query-agent.md`
- `docs/plans/modules/agent-suite-ops.md`

每份模块计划均定义模块边界、前置决策、子阶段、产物、验证、禁止硬编码、风险、停止条件和回滚方式。模块计划不得覆盖仓库内真源规格。

## 6.2 企业开发标准

- 后端骨架：`agent-suite-ops/docs/standards/backend-project-layout.md`
- 数据库：`agent-suite-ops/docs/standards/database-standards.md`
- 代码与注释：`agent-suite-ops/docs/standards/code-and-comment-conventions.md`
- 前后端顺序：`agent-suite-ops/docs/standards/development-sequence.md`
- 企业项目对比：`agent-suite-ops/docs/architecture/enterprise-comparison.md`

`FOUND-010` 必须严格按 `docs/plans/phases/FOUND-010-enterprise-foundation.md` 执行，且仅在 DESIGN-002 完成并经用户确认后开始。

## 7. 总体验收标准

- 三个 Agent 均可单独构建、启动、测试和部署。
- 统一前端不依赖 Agent 内部实现，只依赖版本化 API 契约。
- 单个 Agent 下线不阻止其他两个 Agent 独立运行。
- DeepSeek、MySQL、飞书等外部依赖均可通过适配层替换或禁用。
- 智能问数使用数据库只读账号，LLM 输出未经结构化校验不得执行。
- 所有关键工作流具有失败、重试、取消、幂等和审计设计。
- 课件原始要求、迁移后的实现和自主扩展在报告中分别标注。
- 没有真实密钥、Token、生产配置或隐私数据进入 Git。

## 8. 不做事项

- 不保留 Dify 作为运行时依赖。
- 不构建三个 Agent 之间的自动协作或互相调用。
- 不在当前阶段安装依赖、接入真实外部服务或编写业务代码。
- 不自动创建远程仓库、提交、推送或发布。
- 不把实验 Mock 描述为生产实现。
