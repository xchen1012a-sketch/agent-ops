---
name: documentation-observability
description: 决策文档和可观测性。用于 ADR、API/契约说明、发布说明、结构化日志、指标、追踪和线上可诊断性。
---

# Documentation Observability

## 目标

只记录会影响协作和后续维护的事实，同时让系统出问题时能被定位。文档解释为什么，日志和指标证明发生了什么。

## 适用场景

- 架构选择、阶段切换、跨仓协作、公共 API 变化。
- L3/L4 任务需要契约、验收证据或回归清单。
- 后台任务、外部服务、异步流程、导入导出、媒体流水线。
- 需要日志、指标、trace、request id、run id、job id。

## 不适用场景

- L0/L1 默认不更新 docs。
- 临时代码、实验草稿、未确认方案。
- 文档会替代验证时不要使用本 skill。

## 最小上下文

1. 本次决策或行为变化。
2. 受影响 API、任务、数据、用户路径。
3. 现有 docs/plans/contracts/checklist。
4. 现有日志、监控、错误处理模式。

## 工作流

### 文档工作流

1. 先判断是否必须写文档：API/DB/权限/阶段/跨仓/外部服务才默认需要。
2. 写事实，不写流水账。
3. ADR 只记录重要决策：背景、选择、取舍、后果、回滚方式。
4. API 文档记录请求、响应、错误、兼容性和示例。
5. phase/current 只记录阶段状态和验收证据。
6. 不为小改更新 project-plan。

### 可观测工作流

1. 定义关键事件：request、job、run、export、callback、failure。
2. 使用结构化日志字段，不拼大段自然语言。
3. 每条链路保留 correlation id：request_id、run_id、job_id 或 trace_id。
4. 指标优先 RED：rate、errors、duration；资源类用 USE：utilization、saturation、errors。
5. 避免高基数字段做 metric label，例如 user input、file path、prompt 原文。
6. 日志不输出密钥、token、完整 prompt、隐私数据和原始文件内容。

## 文件边界

- `docs/plans/` 只放总计划、current 和阶段验收；不写实现细节流水账。
- `docs/contracts/` 只放 API、事件、数据和集成契约；不得混入临时讨论。
- `docs/adr/` 只记录已确认架构决策、取舍、后果和回滚。
- `docs/runbooks/` 记录启动、排障、回滚和运维步骤。
- `logs/`、`traces/`、`metrics/` 只记录运行证据；不得提交真实敏感日志。
- 可观测字段必须能关联 request/job/run/node；不要只写自然语言摘要。

## 停止条件

- 用户明确不希望写文档。
- 需要记录敏感信息才能解释问题。
- 还没有完成验证，不能把计划写成已完成。
- 可观测字段会泄露用户数据或密钥。

## 验证方式

- 文档必须指向真实变更和验收证据。
- 日志/指标字段要能回答：谁、何时、做了什么、结果如何、失败原因。
- 最终说明更新了哪些文档或为什么没有更新。
## 强制执行规则

- 遵守 `.ai-rules/skill-contract.md`。
- 本 skill 的工作流、停止条件和验证方式优先于通用建议。

