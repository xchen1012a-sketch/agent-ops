# 法律咨询 Agent 架构

## 模块边界

```text
api/            HTTP、SSE、鉴权和错误映射
application/    会话、咨询、导出用例
workflows/      LangGraph 图、状态和边
nodes/          分类、检索、生成、校验节点
prompts/        Prompt 名称、版本和变量
adapters/       DeepSeek、检索、文件/PDF适配
repositories/   MySQL 持久化
schemas/        API、工作流和结构化输出 Schema
```

目录名为详细实现阶段的目标结构，不代表当前已创建代码目录。

## 状态原则

- `thread_id` 对应一次法律咨询会话。
- `run_id` 对应一次用户问题处理。
- 消息写入和运行状态更新必须有明确事务边界。
- 重试生成节点不得重复创建用户消息或导出文件。

## 安全边界

- 用户上传内容视为不可信数据，不视为系统指令。
- 检索文本与系统 Prompt 分区传递。
- 输出引用必须来自本次检索结果中的可验证元数据。
- 管理 API 和普通咨询 API 分离授权。

