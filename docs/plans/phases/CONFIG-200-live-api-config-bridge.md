# CONFIG-200 配置中心 ↔ 流式 adapter 打通（无 key 回退）

## 状态

- 状态：已确认，执行中
- 日期：2026-07-06
- 任务等级：L3（外部服务 adapter、按账号配置解析、前后端联调）
- 前置：STREAM-100 阶段 1-4 已完成（三 agent 两层 SSE + thinking，前端三页接入）
- 关系：本阶段是三-模块效果计划 §1.2「配置中心存了 key 但 adapter 不读」断点的修复，等价于 STREAM-100 阶段5 的「无 key、单测验证」版；真实 key 端到端联调（打 api.deepseek.com）仍后置。

## 目标

让「配置中心（每账号加密存 DeepSeek key）→ 流式 adapter」这条链打通：
- 某账号在配置页 **启用且填了 DeepSeek key** → 流式端点走真实 DeepSeek `stream()`（读该账号配置）。
- 未填 / 未启用 / 解密失败 → 自动回退 `FakeLlmAdapter`，行为与现在一致。
- 全程**不需要真实 key、不打真实网络**：真实 adapter 用可注入的假 HTTP 客户端做单测验证 SSE 解析与字段分类。

## 已确认决策

1. UI：只在配置页表格加**精简的「生效来源」列**（deepseek 行按 `enabled && api_key_hint` 显示「真实/模拟」），不做会话页徽标。
2. recruitment 流式端点补 `X-User-Subject` 身份头，以支持按账号读配置。
3. 同一 DeepSeek key 需按 agent 各填一次（三库隔离，ADR 既定）——不改设计，仅在 UI 文案提示一句。

## 依据（接口已核实）

- `AgentApiConfigRepo.get_by_type(subject, "deepseek")` → 含 `enabled/base_url/model/api_key_encrypted/timeout_seconds/max_retries`。
- `ApiConfigCrypto.decrypt(token)`（`application/services/agent_api_config.py:36`）。
- `settings.llm_stream_thinking_field_names / llm_stream_answer_field_names`（STREAM-100 已加）。
- 现有非流式 `DeepSeekAdapter.complete`（`infrastructure/llm/deepseek_adapter.py`）作 HTTP 注入模式参考。

## 分阶段（每阶段停下汇报）

### A1 · data-query 样板（后端）
- 新增 `infrastructure/llm/deepseek_stream_adapter.py`：`DeepSeekStreamAdapter.stream()`，注入式流式 HTTP 客户端（Protocol + httpx 实现），按 `settings` 字段名把 `choices[0].delta` 的字段分类成 thinking/answer 分块，HTTP/网络错误转 `LlmStreamError`。
- 新增 `application/services/stream_adapter_resolver.py`：`resolve_stream_adapter(subject, repo, settings)` —— enabled 且有 key 且解密成功 → 真 adapter；否则 `FakeLlmAdapter`。crypto 在解析器内按需构造，主密钥缺失/解密失败 → 回退 fake（不 500）。
- 改 `api/dependencies.py`：`get_llm_stream_adapter` 改为异步、经解析器（依赖 subject + repo + settings）。
- 单测：`test_deepseek_stream_adapter.py`（假 HTTP 客户端验证 reasoning→thinking、content→answer、错误→run.failed 前的 LlmStreamError）、`test_stream_adapter_resolver.py`（有 key→真 / 无 key / 停用 / 坏密钥→fake）；`test_run_stream_live.py` 覆盖 `get_llm_stream_adapter` 为 fake 以保持无 DB。

### A2 · UI 生效来源（前端）
- `ApiConfigAdminPage.vue` 表格加「生效来源」列：deepseek 行按 `enabled && api_key_hint` 显示「真实/模拟」，其余行显示「—」；表说明文案补一句「同一 key 需在每个 Agent 各配置一次」。
- 验证：vue-tsc / eslint / build。

### A3 · legal（后端）
- 复制 A1 的 adapter + resolver；`get_legal_stream_adapter` 经解析器；legal 端点思考通道接真 adapter（真链路时思考来自真实 reasoning，无 key 仍回退现有 fake 思考 + 确定性答复）。
- 单测同构。

### A4 · recruitment（后端）
- 复制 A1；**流式端点补 `X-User-Subject` 身份头**（现无身份）→ `get_recruitment_stream_adapter` 经解析器读该账号配置。
- 单测同构 + 端点带身份头。

## 不做事项

- 不填真实 key、不打真实 DeepSeek 网络（那是后续联调）。
- 不改配置存储/编辑 UI 与加密存储。
- 不加配置缓存（每请求读一次）。
- 不跨 agent 共享 adapter/resolver（复制，不 import）。
- 不改旧端点与其它业务。

## 验证与回滚

- 每阶段 `ruff`/`mypy`/`pytest`（后端）或 `vue-tsc`/`eslint`/`build`（前端）。
- 未填 key 时行为与现状完全一致（回退 fake），可随时回滚（删新增 adapter/resolver、还原 dependency 即回现状）。

## 执行记录

- 2026-07-06：创建计划；UI 精简为配置页单列、recruitment 补身份头，均已确认。待执行 A1。
- 2026-07-06：**A1（data-query 样板）完成**。
  - 新增 `infrastructure/llm/deepseek_stream_adapter.py`（注入式流式 HTTP、按 settings 字段名分类 thinking/answer、错误转 LlmStreamError）。
  - 新增 `application/services/stream_adapter_resolver.py`（enabled+可解密 key→真 adapter；无配置/停用/无 key/主密钥缺失/解密失败→FakeLlmAdapter）。
  - 改 `api/dependencies.py`：`get_llm_stream_adapter` 改为异步经解析器（subject+repo+settings）；移除直接 FakeLlmAdapter 依赖。
  - 单测：`test_deepseek_stream_adapter.py`（reasoning→thinking/content→answer、脏行忽略、传输错误→LlmStreamError）、`test_stream_adapter_resolver.py`（6 分支）、`test_run_stream_live.py` 覆盖 adapter 为 fake 保持无 DB。
  - 验证：`ruff` 0；`pytest`（deepseek 4 + resolver 6 + run_stream_live 2 + sse_forwarder 5）**17 passed**；`mypy` 改动文件零错误，仅未改动的 `agent_api_config.py:52` 既有基线错误。
  - 未验证：真实 key 端到端打 DeepSeek（无 key，回退 fake，行为不变）。
- 2026-07-06：**A2（配置页「生效来源」列）完成**。`ApiConfigAdminPage.vue` 加 `effectiveSource`（deepseek 行 enabled+hint→真实/模拟，余行—）+ 表格列 + 精简文案；`vue-tsc`/`eslint`/`build` 通过，配置页既有单测 3 passed。
- 2026-07-06：**A3（legal）完成**。复制 `deepseek_stream_adapter`+`stream_adapter_resolver`；`get_legal_stream_adapter` 改异步经解析器（user_public_id+repo+settings）；端点测试覆盖 adapter 为 fake。`ruff` 0、`pytest` 13 passed、`mypy` 改动零错误（仅基线 agent_api_config.py:52）。
- 2026-07-06：**A4（recruitment）完成，CONFIG-200 收官**。复制样板；`get_recruitment_stream_adapter` 改异步经解析器；流式端点经 adapter 依赖链要求 `X-User-Public-Id` 身份头；前端 `recruitment.ts` `createRunCompletionStream` 补身份头（`buildRecruitmentStreamHeaders`）。`ruff` 0、`pytest` 10 passed、前端 `vue-tsc`/`eslint`/`build` 通过；`mypy` 改动文件零错误。
  - 独立问题（非本阶段引入）：`workflows/recruitment_nodes.py:139-140` 调用未定义的 `_redact_sensitive_fields`（fairness 主路径 latent bug），已挂后台任务 task_46e7bc78，未在本阶段修改。
- 2026-07-06：**CONFIG-200 全部完成**。三 Agent 流式 adapter 均按账号读配置中心：填了 enabled 的 DeepSeek key → 真实流式；否则回退 fake（行为不变）。真实 key 端到端联调后置。
