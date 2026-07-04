# ADR-0005：LangGraph底座与Deep Agents可选扩展

- 状态：已确认
- 日期：2026-07-04

## 背景

三个Agent默认使用LangGraph。用户要求保留后续接入Deep Agents的选择，最终依据各业务的复杂度、评测结果、安全边界和维护成本决定。

## 决策

- LangGraph是稳定运行时和编排底座，API、Thread/Run语义、State/事件契约不依赖Deep Agents。
- 默认实现为显式自定义LangGraph，尤其适用于智能问数等确定性和安全约束强的流程。
- Deep Agents作为可选harness，仅在需要长任务规划、上下文卸载、文件系统、子Agent或复杂人工审批时评估。
- 不提前安装Deep Agents，不同时维护两套实现，不在业务代码中散落框架判断。
- 每个Agent通过单一graph factory暴露编译后的图；若选用Deep Agents，由factory创建对应图，API和领域契约保持不变。
- 是否启用按模块独立决策，必须通过相同验收样本、轨迹、安全、成本和延迟对比。

## 选择门槛

只有满足以下至少一项且评测收益明确时才引入Deep Agents：

- 任务需要动态规划和多步骤分解，固定图明显难以维护。
- 需要大量文档/工具输出的上下文管理。
- 需要隔离上下文的子Agent委派。
- 需要文件系统/沙箱工具或复杂human-in-the-loop。

简单分类、检索、结构化输出、受限工具链和NL2SQL安全查询优先使用自定义LangGraph。

## 安全约束

Deep Agents具有文件、工具和潜在执行能力时，权限必须在工具、adapter和沙箱层强制限制，不能依赖模型自律。智能问数不得因接入Deep Agents绕过SQL AST、MCP只读账号、表列白名单或查询限制。

## 回滚

保留相同Run/Thread API、领域ports和评测集。若Deep Agents未达到收益或安全门槛，graph factory切回自定义LangGraph实现，数据库和前端契约不变。

## 官方依据

- https://docs.langchain.com/oss/python/deepagents/overview
- https://github.com/langchain-ai/deepagents

