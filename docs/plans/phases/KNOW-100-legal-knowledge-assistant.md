# KNOW-100 Legal Knowledge Assistant

## Status

Backend MVP completed on 2026-07-06. Final report wording and optional screenshots are handled in KNOW-400.

## Goal

让法律助手基于课程法律咨询系统资料和最小法律知识 seed，完成可演示法律咨询链路：提问、分类、结构化回答、最近咨询、报告证据。

## Source Boundary

- 当前课程资料存在于 `docs/homework/AI编程_智能问数实训(课件)/03_AI法律咨询系统实战/`。
- 当前实现使用项目内最小课程模板知识 seed，不声明完整法规全文库。
- 如果没有可验证法规原文，回答中只能声明“课程模板/通用建议/待补充法规原文”，不能虚构具体法条引用。

## Scope Completed

- 新增 `agents/legal-consulting-agent/src/legal_consulting_agent/workflows/legal_knowledge_seed.py`。
- 覆盖劳动、合同、婚姻家庭、刑事、通用 5 类课程模板 seed。
- `retrieval_node` 在没有外部检索适配器输入时使用课程模板 seed。
- 显式传入 `mock_chunks=[]` 时仍保留无来源测试路径。
- seed 引用来源统一标注为课程模板知识包和“待补充法规原文”状态。
- 继续复用已有消息持久化、最近咨询和报告链路。

## Acceptance

- 法律助手能保存并展示最近咨询。
- 回答包含分类、风险、建议、知识来源状态和免责声明。
- 不输出没有来源的具体法规条文。
- 后续报告可覆盖实训模块一“AI 法律咨询系统”的架构、核心代码、测试和运行截图要求。

## Verification Evidence

Run from `C:\Users\ahua\Desktop\agent\agents\legal-consulting-agent`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_legal_workflow.py -q
```

Result recorded in KNOW-100 execution: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_question_answer_service.py tests\unit\test_generation_prompt_service.py tests\unit\test_prompt_workflow_factory.py tests\unit\test_workflow_runner_service.py -q -p no:cacheprovider --basetemp .\.pytest-basetemp-know100
```

Result recorded in KNOW-100 execution: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit -q -p no:cacheprovider --basetemp .\.pytest-basetemp-know100-all
```

Result recorded in KNOW-100 execution: passed with the existing FastAPI/TestClient deprecation warning.

## Not Done

- 未导入完整法规全文库。
- 未做生产级律师审核后台。
- 未新增复杂 RAG 基础设施。
- 未声明真实外部模型调用一定可用。

## Rollback

- 移除新增法律知识 seed。
- 恢复 `retrieval_node` 到本阶段前的演示回答逻辑。
