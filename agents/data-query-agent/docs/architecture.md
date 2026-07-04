# 智能问数 Agent 架构

## 模块边界

```text
api/            Web运行、查询历史、评测和飞书入口
application/    查询、评测、审计用例
workflows/      LangGraph 图、状态和恢复点
nodes/          意图、检索、SQL生成、安全、执行、解读节点
prompts/        NL2SQL与结果解读Prompt版本
policies/       SQL AST与查询资源策略
adapters/       DeepSeek、MySQL、Schema目录、飞书、图表适配
repositories/   运行态、审计与反馈持久化
schemas/        问题、SQL候选、结果、图表和事件Schema
```

目录名为详细实现阶段的目标结构，不代表当前已创建代码目录。

## 数据访问

业务查询和 Agent 运行态写入使用不同连接与权限：

- Query connection：仅能读取允许的业务表/视图。
- State connection：只能读写 Agent 自身运行态表。

即使开发环境位于同一 MySQL 实例，也不得复用高权限账号。

## 确定性边界

- LLM 负责理解问题、选择指标和生成候选结构。
- 代码负责 Schema 校验、AST 策略、数据库执行和数值格式化。
- 最终回答中的关键数字必须来自查询结果，不允许模型重算后静默改变。
- 图表数据引用结构化查询结果，不从自然语言回答反向解析。

## 恢复与幂等

- 数据库查询节点只读，可在同一输入和数据快照下安全重试。
- 飞书消息按 `message_id` 去重。
- SSE 和飞书卡片更新使用递增序号，重复事件不得重复追加。

