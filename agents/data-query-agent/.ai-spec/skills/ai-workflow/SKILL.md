---
name: ai-workflow
description: 设计 AI Agent、Skill 和工作流系统。用于节点状态、任务编排、Prompt 版本、LLM 输出安全、重试、恢复、日志和可观测性。
---

# AI Workflow

## 目标

让 AI 工作流可观察、可重试、可恢复、可验证。LLM 是不稳定输入源，不能把它的输出直接当成命令或事实执行。

## 适用场景

- Agent / Skill / Workflow 编排。
- 节点状态机、输入输出 schema、日志和错误处理。
- Prompt 模板版本化。
- 长任务异步、重试、取消和恢复。

## 不适用场景

- 纯前端样式。
- 纯数据库 schema。
- 单次 prompt 文案润色但不涉及系统行为。

## 最小上下文

1. 工作流定义或节点列表。
2. 节点 input/output schema。
3. 状态存储和任务表。
4. LLM 调用封装、Prompt 模板。
5. 日志、错误和测试。

## 工作流

1. 先定义节点边界：职责、输入、输出、失败语义。
2. 节点状态至少包含 `pending`、`running`、`success`、`failed`、`retrying`。
3. 每个节点记录 input、output、logs、error、retry count。
4. LLM 输出必须结构化校验；不能直接执行命令、SQL、FFmpeg 参数或文件路径。
5. Prompt 模板要有名称、版本、输入变量和输出 schema。
6. 长任务必须异步，提供查询、取消、重试能力。
7. 失败要可定位：错误码、节点名、输入摘要、外部服务响应摘要。
8. 恢复逻辑要清楚：从哪个节点恢复，哪些节点幂等。
9. Skill 输入输出要小而明确，不把整个项目上下文塞进一个 skill。

## 状态机建议

```text
pending -> running -> success
pending -> running -> failed -> retrying -> running
running -> failed
running -> canceled
```

## 模块边界

- `workflows/` 只定义流程图、节点列表、边和版本；不得直接执行外部副作用。
- `nodes/` 只实现单节点职责、输入输出 schema 和失败语义。
- `agents/` 负责任务策略和上下文选择；不得绕过节点状态机直接改数据库或文件。
- `skills/` 描述可复用能力；不得把整个项目上下文塞进一个 skill。
- `prompts/` 保存模板、版本、变量和输出 schema；不得散落在业务代码字符串里。
- `runners/`、`executors/` 负责调度、重试、取消、恢复和超时。
- `tools/`、`adapters/` 只封装外部工具调用；LLM 输出必须先校验再传入。
- `traces/`、`logs/`、`events/` 记录节点级证据；不得只存最终摘要。
- `state/`、`stores/` 管理运行态；长期事实仍按数据库规则落库。

## 相邻 Skill 触发

- 节点状态、运行记录、prompt 版本或审计需要持久化时，同时触发 `database`。
- 对外暴露运行、取消、重试、恢复 API 时，同时触发 `backend-api`。
- 节点涉及图片、音频、视频、FFmpeg、TTS 或 ComfyUI 时，同时触发 `media-pipeline`。

## 验证清单

- [ ] 节点状态流转测试。
- [ ] 失败和重试测试。
- [ ] 恢复或幂等性说明。
- [ ] LLM 输出 schema 校验测试。
- [ ] 不直接执行 LLM 输出的断言。
- [ ] 日志能定位到节点和错误原因。

## 输出要求

说明节点边界、状态机、输入输出 schema、失败处理、LLM 安全边界、验证证据和剩余风险。
## 停止条件

- 需要直接执行 LLM 输出的命令或代码。
- 需要接入真实外部模型、队列、工作流引擎或付费服务但用户未确认。
- 节点状态、重试、幂等或取消语义不清。
- 继续实现会把 mock、demo 或实验逻辑伪装成生产能力。
## 强制执行规则

- 遵守 `.ai-rules/skill-contract.md`。
- 本 skill 的工作流、停止条件和验证方式优先于通用建议。


