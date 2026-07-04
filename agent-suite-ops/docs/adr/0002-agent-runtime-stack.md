# ADR-0002：采用 LangGraph + FastAPI Agent 运行栈

- 状态：已确认
- 日期：2026-07-04

## 背景

课件原方案使用 Dify。用户要求迁移到 LangChain 生态自研方案，并优先采用成熟开源工程模式。

## 决策

- LangGraph：工作流状态、节点编排、重试、恢复和流式事件。
- FastAPI + Pydantic v2：独立 Agent API 和 OpenAPI 契约。
- Agent Service Toolkit：仅作为工程结构参考，不直接复制无关的 Streamlit 或供应商功能。
- Agent Protocol：借鉴 thread、run、stream、cancel 等 API 语义。
- 不使用已弃用的 LangServe。

## 后果

- 每个 Agent 明确定义状态 Schema 和节点失败语义。
- API 不直接暴露 LangGraph 内部对象。
- 框架升级必须先通过契约和轨迹回归测试。

## 回滚

LangGraph 被限制在工作流层；如需替换编排器，保持 API、domain node 和 adapter 契约不变，替换 workflow 实现。

