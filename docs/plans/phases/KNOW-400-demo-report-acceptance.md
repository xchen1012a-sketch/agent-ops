# KNOW-400 Demo Report Acceptance

## Status

Completed for MVP acceptance on 2026-07-06.

## Goal

把法律助手、招聘助手、问数助手三个模块整理成课程 MVP 可提交材料：能本地运行、核心链路可复现、测试或 smoke 证据明确、外部服务边界不虚构。

## Source Boundary

当前 `docs/homework/` 已确认存在以下资料：

- `实训报告大纲.html`：三模块报告结构。
- `AI编程_智能问数实训(课件)/03_AI法律咨询系统实战/`：法律咨询课程资料。
- `AI编程_智能问数实训(课件)/05_Dify工作流智能体开发/dify案例实战/`：Dify 节点案例，包含简历信息提取、答案节点、模板输出等案例。
- `AI编程_智能问数实训(课件)/06_智能问数/`：智能问数、数据字典、宽表、NL2SQL Prompt、端到端案例。
- `AI编程_智能问数实训(课件)/shop_db_export.sql`：课程 SQL 数据材料。
- `AI编程_智能问数实训(课件)/feishu-to-dify/`：飞书到 Dify 示例代码；`.env` 不作为报告证据引用。

当前没有完成或没有证据的内容：

- 未证明真实 Dify 应用已部署并导出。
- 未证明真实飞书租户已完成订阅和端到端回调。
- 未证明真实 DeepSeek Key 可用并完成全链路调用。
- 未证明外部 MySQL `shop_db` 已导入并由 Agent 实时查询。

因此，当前验收口径是本地可运行 MVP，不是生产联调交付。

## Acceptance Summary

| Agent | 当前完成效果 | 验收口径 |
| --- | --- | --- |
| 法律助手 | 有最小课程模板知识 seed，支持法律问题分类、风险提示、建议、来源状态和最近咨询保存 | 课程 MVP 可演示；不声明完整法规库 |
| 招聘助手 | UI 已简化为对话体验，JD/简历输入后输出匹配分、证据、风险点、面试问题、公平性边界 | Dify 等价本地工作流；不声明真实 Dify 部署 |
| 问数助手 | 支持 local-demo 自然语言问数，返回 SQL、安全策略、结果表、解释、图表语义和飞书 mock card 语义 | 本地 deterministic fixture；不声明真实 MySQL/飞书联调 |

## Runtime Smoke

本地运行入口：

- Web：`http://127.0.0.1:7777`
- Legal live health：`/api/legal/v1/health/live`
- Recruitment live health：`/api/recruitment/v1/health/live`
- Data live health：`/api/data/v1/health/live`

已完成 smoke 记录：

- Web 返回 `200`。
- 三个 Agent health 均返回 `{"status":"ok"}`。
- 通过 Vite proxy 登录 `admin@example.com` / `Admin123456` 成功。
- 创建 data thread 返回 `201`。
- `POST /api/data/v1/threads/{thread_id}/runs/local-demo` 返回 `200`，问题为“各渠道销售额排行”时返回 fixture `T2`、允许的 SQL、本地 rows `app/web` 和 bar chart 语义。

## Verification Evidence

| 模块 | 证据 |
| --- | --- |
| 法律助手 | `KNOW-100` 记录了 legal workflow、问答服务、prompt workflow、runner service 的单元测试通过 |
| 招聘助手 | `ruff`、`mypy`、招聘 pytest slice 通过，结果 `35 passed`；前端 typecheck 通过 |
| 问数助手 | `ruff`、`mypy`、问数 pytest slice 通过，结果 `29 passed`；前端 lint/typecheck 通过；local-demo API smoke 通过 |

## Report Material Mapping

| 实训报告章节 | 当前可写内容 |
| --- | --- |
| 第一章 项目概述 | 三 Agent 架构、统一前端、三个后端服务、本地演示边界 |
| 第二章 AI 法律咨询系统 | 法律助手页面、最小知识 seed、结构化回答、最近咨询、测试证据 |
| 第三章 Dify 工作流智能体 | 招聘助手作为 Dify 等价工作流：参数提取、规则校验、LLM 分析、模板报告、答案输出 |
| 第四章 智能问数系统 | `shop_db` 资料、宽表/NL2SQL Prompt、SQL 安全、local-demo 查询、图表、飞书 mock |
| 第五章 总结 | 三模块交付清单、未完成真实外部服务联调、后续扩展方向 |

## Optional Follow-Up

- 如果需要提交正式报告，再基于上述素材生成 DOCX/PDF。
- 如果需要截图，可直接在当前本地服务上截取三张页面图；不是当前代码达标的阻塞项。
- 真实 Dify/飞书/DeepSeek/MySQL 联调作为后续扩展阶段处理。

## Rollback

本阶段只整理报告和验收边界，不新增功能代码。回滚时恢复本文件和 `docs/plans/current.md` 到上一版本即可。
