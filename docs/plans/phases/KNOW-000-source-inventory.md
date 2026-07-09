# KNOW-000 Source Inventory

## Status

Completed on 2026-07-06. Source boundary refreshed during KNOW-400 after the full homework folder was inspected.

## Goal

固定三 Agent MVP 所需知识源、完成标准、项目已有资产、缺口和不得虚构边界，作为后续实现阶段的输入清单。

## Scope

- 盘点 `docs/homework/` 中与法律、招聘/Dify、问数相关的课程资料。
- 盘点当前项目已有 prompt、workflow、API、数据模型和前端入口。
- 输出每个 Agent 的知识文件、补充配置、完成效果和外部服务边界。
- 标注哪些内容当前可直接使用，哪些只能作为后续联调项。

## Source Inventory

| Agent | 可复用课程来源 | 可复用项目资产 | 缺口/边界 |
| --- | --- | --- | --- |
| 法律助手 | `03_AI法律咨询系统实战/`、`实训报告大纲.html` 的 AI 法律咨询系统要求 | 法律会话、报告、prompt loader、workflow、最小知识 seed | 当前不声明完整法规全文库；课程模板 seed 只能证明 MVP 结构 |
| 招聘助手 | `05_Dify工作流智能体开发/dify案例实战/`，尤其简历信息提取、模板输出、答案节点等案例 | 招聘 JD/简历结构化、匹配分析、报告、对话 UI、版本化规则 | 当前是 Dify 等价本地工作流，不声明真实 Dify 部署 |
| 问数助手 | `06_智能问数/`、`shop_db_export.sql`、NL2SQL prompt、飞书接入说明 | data-query schema catalog、indicator、SQL whitelist、AST policy、fixture、Feishu mock | 当前以 local deterministic fixture 验证，不声明真实 MySQL/飞书联调 |

## Not Doing

- 不配置真实 DeepSeek、Dify、飞书或外部 MySQL。
- 不读取或引用 `feishu-to-dify/.env` 里的任何密钥。
- 不把未验证的外部服务结果写成已完成。
- 不把招聘助手的 RAG 候选人库作为 MVP 必需项。

## Acceptance

- 计划书已列出三 Agent 的知识文件、配置要求和完成效果。
- 后续 `KNOW-100`、`KNOW-200`、`KNOW-300`、`KNOW-400` 均按此边界执行。
- 当前 source inventory 已从“只看到大纲和模板”修正为“已看到完整课程课件目录，但外部服务仍未联调”。

## Rollback

恢复本阶段文件到进入 KNOW-000 前版本，并恢复 `docs/plans/current.md` 的阶段指向。
