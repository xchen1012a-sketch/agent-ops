# MVP-001 Homework MVP Shell

## 目标

把当前企业级多智能体平台收敛为作业可演示的 MVP 第一阶段：保留三大课程模块、统一 API 配置和模型流式输出，隐藏与作业主链路无关的后台入口。

## 范围

- 前端侧边栏只展示 MVP 主入口：
  - 法律咨询：开始咨询、咨询记录、法律报告。
  - 智能招聘：招聘任务、新建分析、匹配报告。
  - 智能问数：问数对话、查询历史。
  - 系统配置：API 配置。
- 法律咨询页面改用后端 SSE 问答接口，展示流式输出状态和逐步生成的回答。
- 法律后端 SSE 接口补充 `message.delta` 事件，保持原 `completed` 结果事件。
- 保留已有招聘和问数 SSE 入口，不扩大改动范围。

## 不做

- 不删除路由和页面文件，只从菜单隐藏非 MVP 入口。
- 不接真实 DeepSeek、Dify、MCP、飞书或企业微信密钥。
- 不改数据库结构。
- 不实现飞书桥接和 8 个问数测试面板；后续阶段单独做。
- 不修复与本阶段无关的后台页面。

## 验收标准

- 侧边栏不再显示知识材料、法律分类、用户权限、Prompt 版本、高风险审核、候选材料、评分规则、招聘审计、SQL 审计、偏好设置等非 MVP 入口。
- 法律咨询提交问题时通过 SSE 接收事件，并能看到“正在生成”的流式回答。
- 法律 SSE 测试覆盖 `started`、`message.delta`、`completed`。
- 前端类型检查或聚焦测试通过；若无法运行，记录原因。

## 验证记录

- 2026-07-05：
  - `agents/legal-consulting-agent`: `.venv\Scripts\python.exe -m pytest tests\unit\test_legal_questions_api.py -q` 通过，3 passed；pytest cache 写入受限有 warning，不影响测试结果。
  - `agents/legal-consulting-agent`: `.venv\Scripts\python.exe -m ruff check src\legal_consulting_agent\api\v1\endpoints\legal_questions.py tests\unit\test_legal_questions_api.py` 通过。
  - `agent-suite-web`: `npm.cmd run typecheck` 通过；第一次 `npm run typecheck` 被 PowerShell 执行策略拦截，改用 `npm.cmd` 后成功。
  - 浏览器验证：`/settings/api-config` 侧边栏已只保留 MVP 入口；非 MVP 入口无残留，保留入口无缺失。

## 回滚方式

- 恢复 `agent-suite-web/src/app/AppSidebar.vue` 的原菜单项。
- 恢复 `agent-suite-web/src/views/legal/LegalSessionPage.vue` 使用普通 POST 问答。
- 恢复 `agents/legal-consulting-agent/src/legal_consulting_agent/api/v1/endpoints/legal_questions.py` 只输出 `started` 和 `completed`。
