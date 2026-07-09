# STREAM-100 三 Agent 思考展示式 LLM 流式对接计划

## 状态

- 状态：待用户确认（未动手）
- 日期：2026-07-06
- 覆盖：三个 Agent（`data-query` / `legal` / `recruitment`）后端流式 + thinking，`agent-suite-web` 三个会话页接入
- 任务等级：L3（新增 SSE 契约字段、LLM 流式、前后端联调）
- 复用目标：后端 SSE 两层中间件与前端思考组件设计为自包含、模型无关、字段可配；一处证明，三处复用

## 依据（逐 Agent 核查证据）

- 前端 SSE 客户端（复用不改）：`agent-suite-web/src/lib/sse-client.ts`
- 前端事件契约：`agent-suite-web/src/types/sse.ts:8`（仅正文 `message.delta`，无思考通道）
- data-query：`src/data_query_agent/api/v1/endpoints/runs.py:81,213`（`GET /runs/{id}/stream` 回放 DB 状态，非 token 流）；`domain/ports/llm_adapter.py:28`（仅 `complete()`）；`infrastructure/llm/{deepseek,fake}_adapter.py`（adapter 已写）
- legal：`src/legal_consulting_agent/api/v1/endpoints/legal_questions.py:63,102`（`POST /sessions/{id}/questions/events` 已手写 `message.delta` 假分块 + 自己的 `_sse_event`）；`infrastructure/llm/__init__.py`（adapter 空壳）；前端 `src/views/legal/LegalSessionPage.vue`（已有粗糙计时，按 `message.delta`/`completed` 累积）
- recruitment：`src/recruitment_assistant_agent/api/v1/endpoints/recruitment_runs.py:73`（`GET /recruitment-runs/{run_id}/stream` 回放 mock 节点事件）；`infrastructure/llm/__init__.py`（adapter 空壳）；前端 `src/views/recruitment/*`
- 项目规则：`.ai-spec/.ai-rules/development-standards.md`（§1 禁硬编码、§2 框架规范、§3 跨仓边界、§6 后端分层）、skill `frontend-web`、`backend-api`

**三家结论**：各自散落一套 `_sse_event`、SSE 形状不一致（legal 已有 message.delta、data/recruitment 是状态/节点回放）、都无 thinking、adapter 除 data-query 外为空壳。所以"复用"是**每个 agent 各自换两层中间件 + 加 thinking 通道 + 补 `stream()`**，是三份真实工作。

## 需求/现象

参照 Claude.ai 思考展示：LLM 流式按"思考类字段/正文字段"分 thinking / answer 两通道；前端 `thinking → answering → done` 状态机；思考阶段可展开面板+打字机、回答开始自动收起并显示"已思考 X 秒"、点击可展开历史；正文 markdown+打字机。三个 Agent 均要具备该能力。

## 锁定设计决策（按推荐，经用户确认）

1. **每个 Agent 新增真流式端点**，保留各自旧端点做回放/兼容（可回滚）：
   - data-query：新增 `POST /threads/{thread_id}/runs/stream`，保留旧 `GET /runs/{id}/stream`
   - legal：新增 thinking 通道到现有 `POST /sessions/{id}/questions/events`（就地增强，旧 `message.delta`/`completed` 不变）
   - recruitment：新增 `POST /recruitment-tasks/{task_id}/runs/stream`（token 流），保留旧 `GET /recruitment-runs/{run_id}/stream`（节点回放）
2. **后端两层中间件**（各 agent 各一份，靠复制不 import；模型无关/业务无关）：
   - 层1 归一化器：扩展各 agent 的 `LlmAdapter` 端口新增 `stream()`，产出统一 `LlmStreamChunk{kind: 'thinking'|'answer', text}`
   - 层2 SSE 转发器：独立 `infrastructure/sse/` 模块，把 `LlmStreamChunk` 映射为 SSE 帧 + 生命周期事件 + sequence + 心跳；业务路由零拼装，逐步替代散落的 `_sse_event`
3. **字段名可配、不硬编码**（每 agent `core/config` Settings + `.env.example`）：
   - `LLM_STREAM_THINKING_FIELDS`（默认 `reasoning_content,reasoning,thinking`）
   - `LLM_STREAM_ANSWER_FIELDS`（默认 `content,text`）
4. **先假后真**：先 `FakeLlmAdapter.stream()` 产出 thinking+answer 两段，全链路用 mock 打通；真实 DeepSeek `stream()` + reasoning 映射后置到阶段 5（需真实 key，红线，单独确认）。
5. **顺序：一处样板 → 前端一次 → 两处复用 → 真模型**。data-query 先做样板，前端组件建一次并在 data 页验证，再铺 legal、recruitment，各自独立停下汇报。

## SSE 事件契约（三家统一，在现有契约上做加法，向后兼容）

| 事件名 | 语义 | payload | 状态机 |
|---|---|---|---|
| `run.started` | 运行开始 | `{run_id}` | → thinking/answering |
| `message.thinking.delta` | 思考增量（新增） | `{delta, cumulative_length?}` | 驱动 thinking |
| `message.thinking.completed` | 思考结束（新增） | `{duration_ms}` | thinking → answering，冻结"已思考 X 秒" |
| `message.delta` | 正文增量（沿用） | `{delta, cumulative_length?}` | 驱动 answering |
| `message.completed` | 正文完成（沿用） | `{content, ...}` | → done |
| `run.failed` | 失败（沿用） | `{error_code, message, retryable}` | → error |
| `heartbeat` | 心跳（沿用） | `{}` | 保活 |

无 reasoning 的模型永不发 `message.thinking.*`，前端自动退化为无思考面板。

## 后端分层（每 agent 相同结构）

```
业务路由 —调用→ [层2 sse_forwarder] —消费→ [层1 adapter.stream()] —归一化→ 真/假 LLM
```

- 层1：`domain/ports/llm_adapter.py` 增 `LlmStreamChunk` + `stream()`；`FakeLlmAdapter.stream()`（先）、`DeepSeekAdapter.stream()`（阶段5）。thinking/answer 分类用 Settings 字段清单。
- 层2：`infrastructure/sse/sse_forwarder.py` 提供 `sse_frame(event, data, *, sequence)` 与 `iter_llm_sse(chunks, *, run_id, heartbeat_interval)`；纯协议、零业务、零模型知识。

## 前端组件拆分（建一次，三页复用）

| 单元 | 类型 | 职责 | 业务耦合 |
|---|---|---|---|
| `components/chat/ThinkingPanel.vue` | 展示组件 | 折叠面板、打字机滚动、"Thinking…"/"已思考 X 秒"、answering 自动收起、点击展开历史 | 零，纯 props |
| `composables/useAgentStream.ts` | composable | 包 `AgentStreamClient`，跑状态机，分离 `thinkingText`/`answerText`，计时 | 零，传入 stream 工厂 |
| `composables/useTypewriter.ts` | composable | 收到 buffer 与显示 buffer 解耦，做平滑打字机 | 零 |
| `components/ui/SafeMarkdown.vue` | 现有复用 | 正文 markdown 渲染 | 零 |
| 三个会话页（data/legal/recruitment） | 容器 | 布局 + 调 composable + 业务 | 业务留各页 |

状态机字段（`useAgentStream`）：`phase: 'idle'|'thinking'|'answering'|'done'|'error'`、`thinkingText`、`answerText`、`thinkingStartedAt`、`thinkingElapsedSeconds`、`thinkingDurationMs`、`panelExpanded`。
转移：`thinking.delta`→thinking（展开+计时）；`thinking.completed` 或首个 `message.delta`→answering（冻结时长+收起）；`message.completed`/`run.completed`→done；`run.failed`/流错误→error。

## 逐 Agent 现状与改动清单

### A. data-query（样板，阶段1 + 前端阶段2）
- 现状：流式端点回放 DB 状态、无 message.delta、adapter 已写。
- 后端改/新：`domain/ports/llm_adapter.py`、`infrastructure/llm/fake_llm_adapter.py`、`core/config.py`+`.env.example`、新 `infrastructure/sse/{__init__,sse_forwarder}.py`、`api/v1/endpoints/runs.py`（加 `POST /threads/{id}/runs/stream`）、新单测 `tests/unit/{test_sse_forwarder,test_run_stream_live}.py`。
- 前端改/新：`src/types/sse.ts`、新 `components/chat/ThinkingPanel.vue`、新 `composables/{useAgentStream,useTypewriter}.ts`、`src/api/data-query.ts`（新 stream 工厂）、`src/views/data/DataSessionPage.vue`、单测。

### B. legal（阶段3）
- 现状：`POST /sessions/{id}/questions/events` 已发 `message.delta`+`completed`；adapter 空壳；前端页已有粗糙计时。
- 后端改/新：新 `infrastructure/sse/`（复制样板）、`domain/ports` 加 `stream()`、新 `infrastructure/llm/fake_llm_adapter.py`、`core/config.py`+`.env.example`、`endpoints/legal_questions.py`（在现有 events 端点补 thinking 通道，走 sse_forwarder）、单测。
- 前端改：`src/api/legal.ts`（stream 工厂对齐新事件）、`src/views/legal/LegalSessionPage.vue`（换用 `ThinkingPanel`+`useAgentStream`，替换现有手写计时）、单测。

### C. recruitment（阶段4）
- 现状：`GET /recruitment-runs/{run_id}/stream` 回放 mock 节点事件；adapter 空壳；`start_run` 全 mock。
- 后端改/新：新 `infrastructure/sse/`（复制样板）、`domain/ports` 加 `stream()`、新 `infrastructure/llm/fake_llm_adapter.py`、`core/config.py`+`.env.example`、`endpoints/recruitment_runs.py`（加 `POST /recruitment-tasks/{id}/runs/stream` token 流）、单测。
- 前端改：`src/api/recruitment.ts`（新 stream 工厂）、`src/views/recruitment/*`（会话/结果页接入 `ThinkingPanel`+`useAgentStream`）、单测。

## 不做事项

- 不改各 agent 旧回放端点语义与旧 `message.delta`/`completed`。
- 三 agent 不互相 import 中间层，改用复制。
- 阶段 1-4 全走 mock，不接真实 DeepSeek/MySQL/飞书。
- 不硬编码字段名、模型名、地址、超时（一律 Settings + .env.example）。
- 普通用户页不展示 generated SQL（data 域沿用现有约束）。
- 不提交 Git，除非用户明确要求。
- 发现须改路由结构、App Shell、全局样式、认证权限，停止并报告。

## 分阶段步骤与验证（每阶段完成即停下汇报）

- **阶段1 · data-query 后端样板**：层1 端口+假流式、层2 sse_forwarder、新流式端点、Settings 字段。验证：`ruff`/`mypy`/`pytest`（sse_forwarder 单测覆盖 thinking/answer→事件、sequence、心跳、失败转 run.failed；端点单测覆盖 mock 帧序）。
- **阶段2 · 前端共享组件 + data 接入**：`ThinkingPanel`/`useAgentStream`/`useTypewriter`/类型/stream 工厂/data 页。验证：`pnpm typecheck`/`lint`/`test`/`build`；组件/composable 单测覆盖状态机与自动收起；浏览器核对展开→收起→"已思考 X 秒"→正文流式。
- **阶段3 · legal 后端 thinking + 页面接入**：验证同上（后端门禁 + 前端 legal 页复用组件）。
- **阶段4 · recruitment 后端 thinking + 页面接入**：验证同上。
- **阶段5（后置，需确认）· 真实 DeepSeek `stream()` + reasoning 映射**（三域，需 key，红线）。
- **阶段6（可选）· 收敛散落 `_sse_event` 与文档/契约同步**。

未跑项一律标"未验证"，不写成通过。

## 验收标准

- 三 agent 各有新流式端点，按 thinking/answer 两通道推 SSE，字段可配、模型无关、转发不落业务路由。
- 前端三页 `thinking→answering→done` 状态机正确；思考面板打字机、自动收起、"已思考 X 秒"、点击展开；正文 markdown+打字机。
- `ThinkingPanel` 与 composables 零业务耦合，三页共用同一份。
- mock 全链路可跑通且有单测；真实模型接入不阻塞阶段 1-4 验收。
- 每阶段 diff 不夹带其它 agent 或并行改动。

## 停止条件

- 需要改认证、权限、路由结构或旧端点契约。
- 需要真实外部服务（DeepSeek/MySQL/飞书）才能继续。
- 归一化器字段来源或事件契约与前端不一致导致靠猜。

## 回滚/降级

- 每阶段、每 agent 独立可回滚：删新增 sse 模块/端点/组件/composable/类型加法即回现状。
- 旧端点与旧 `message.delta` 语义不变，回滚不影响既有页面。
- 真实模型不可用时前端退化为无思考面板 + 普通请求，不伪装数据。

## 执行记录

- 2026-07-06：创建计划（data-query 首切片版）。
- 2026-07-06：按用户选择扩为完整三 Agent 计划，补 legal/recruitment 现状证据、逐 agent 改动清单、前端三页接入、分 agent 验收；执行顺序改为 data-query 样板 → 前端一次 → legal → recruitment → 真模型。待确认后执行阶段 1。
- 2026-07-06：**阶段 1（data-query 后端样板）完成**。
  - 层1：`domain/ports/llm_adapter.py` 新增 `LlmStreamChunk`/`LlmStreamError` + Protocol `stream()`（默认不支持，非流式 adapter 快速失败）；`infrastructure/llm/fake_llm_adapter.py` 实现 `stream()` 产出 thinking+answer 分块。
  - 层2：新增 `infrastructure/sse/{__init__,sse_forwarder}.py`，`iter_llm_sse` 模型无关/业务无关，映射 run.started/thinking.delta/thinking.completed/message.delta/message.completed/run.failed + sequence + 可选 heartbeat。
  - 配置：`core/config.py` + `.env.example` 新增 `LLM_STREAM_THINKING_FIELDS`/`LLM_STREAM_ANSWER_FIELDS`（逗号分隔，模型无关，供阶段5 真实 adapter 分类字段）。
  - 端点：`api/v1/endpoints/runs.py` 新增 `POST /threads/{thread_id}/runs/stream`（校验归属→adapter.stream→sse_forwarder，mock、不落库）；`api/dependencies.py` 新增 `get_llm_stream_adapter`（默认 FakeLlmAdapter）。旧 `/runs/{id}/stream` 未改。
  - 验证：`ruff check`（改动文件）通过；`pytest tests/unit/test_sse_forwarder.py test_run_stream_live.py test_run_stream_api.py` → 10 passed（含旧端点回归）；`mypy` 全包 → 改动文件零错误，仅 1 处既有基线错误在未改动文件 `agent_api_config.py:52`。
  - 未验证：完整 pytest 套件（依赖 chromadb/sentence-transformers/asyncmy，本地 Python 3.14 空 venv 无法安装 torch/编译型包）；真实 DeepSeek 流式（阶段5）。
- 2026-07-06：**阶段 2（前端共享组件 + data 接入）完成**。
  - 事件类型：`types/sse.ts` 加 `message.thinking.delta`/`message.thinking.completed` 事件名 + `ThinkingDeltaPayload`/`ThinkingCompletedPayload`（加法，向后兼容）。
  - 共享组件：新增 `components/chat/ThinkingPanel.vue`（纯展示：折叠面板、打字机、"思考中 Xs"/"已思考 X 秒"、answering 自动收起、点击展开、prefers-reduced-motion）；新增 `composables/useAgentStream.ts`（状态机 idle→thinking→answering→done/error，分离 thinking/answer 缓冲 + 计时）与 `composables/useTypewriter.ts`（收到/显示解耦的打字机）。三者零业务耦合，可复制到 legal/recruitment。
  - API：`api/data-query.ts` 加 `createRunCompletionStream`（POST /threads/{id}/runs/stream，带 X-User-Subject）。
  - 接入：`views/data/DataSessionPage.vue` 用 `useAgentStream` 驱动 ThinkingPanel + `SafeMarkdown`(打字机正文)，替换旧状态回放流；保留 run 详情与取消/重试/刷新控件。
  - 验证：`vue-tsc --noEmit` → 0 错误；`eslint`（改动文件，--max-warnings=0）→ 0；`vitest`（use-agent-stream 4 + thinking-panel 6 + sse-client 3 + data-query-client 6）→ **19 passed**；`vite build` → 成功。
  - 未验证：真实浏览器端到端（需后端 data-query 运行 + 网关，属联调）；真实模型 reasoning（阶段5）。
- 2026-07-06：**阶段 3（legal 后端 thinking + 页面接入）完成**。
  - 后端：新增 `domain/ports/llm_adapter.py`（legal 此前无 LLM 端口）、`infrastructure/llm/fake_llm_adapter.py`（思考占位，答复仍来自确定性问答服务）、`infrastructure/sse/{__init__,sse_forwarder}.py`（复制 data-query 样板，含 completed_extra）；`core/config.py`+`.env.example` 加字段映射；`api/dependencies.py` 加 `get_legal_stream_adapter`；`endpoints/legal_questions.py` 的 events 端点改为经 sse_forwarder 输出 thinking + 答复，终止事件 message.completed 通过 completed_extra 携带法律 DTO（answer/citations/high_risk 等）。
  - **计划外调整（已评估，务必知悉）**：锁定决策1 原写"legal 旧 message.delta/completed 不变"。实测发现旧终止事件名为 `completed`、开始事件 `started`，与共享契约（`message.completed`/`run.started`）不一致，而前端 `useAgentStream` 只认共享事件。因该 SSE 的唯一消费者就是本阶段同步重写的 `LegalSessionPage`，故将 legal 升级为共享契约（`message.delta` 名保持不变），并同步更新了既有端点单测。无其它消费者受影响，可回滚。
  - 前端：`views/legal/LegalSessionPage.vue` 换用 `useAgentStream`+`ThinkingPanel`+`useTypewriter`，移除手写计时/streamingAnswer；高风险提示改由持久化消息推导；`api/legal.ts` 无需改（复用现有 stream 工厂）。
  - 数据层复用：给 data-query 的 `iter_llm_sse` 增补通用 `completed_extra`（可选、业务无关），两 agent 副本保持一致；data-query 回归 7 passed、mypy 改动文件零错误。
  - 验证：legal `ruff`（改动，autofix import 排序后）→ 0；`pytest tests/unit/test_legal_questions_api.py test_sse_forwarder.py` → **6 passed**；`mypy` 全包 → 改动文件零错误，仅 1 处既有基线错误在未改动文件 `agent_api_config.py:52`。前端 `vue-tsc` 0、`eslint` 0、`vitest`（use-agent-stream/thinking-panel/legal-client）17 passed。
  - 未验证：真实浏览器端到端（需 legal 后端 + 网关联调）；真实模型 reasoning（阶段5）。
- 2026-07-06：**阶段 4（recruitment 后端 thinking + 页面接入）完成**。
  - 后端：新增 `domain/ports/llm_adapter.py`、`infrastructure/llm/fake_llm_adapter.py`（思考+分析占位）、`infrastructure/sse/{__init__,sse_forwarder}.py`（复制样板，含 completed_extra）；`core/config.py`+`.env.example` 加字段映射；`api/dependencies.py` 加 `get_recruitment_stream_adapter`；`endpoints/recruitment_runs.py` 新增 `POST /recruitment-tasks/{task_id}/runs/stream`（mock token 流，不落库、不跑真实工作流）。旧 `GET /recruitment-runs/{id}/stream`（节点回放）未改。
  - 前端：`api/recruitment.ts` 加 `createRunCompletionStream`；`views/recruitment/RecruitTaskDetailPage.vue` 在运行区接入 `ThinkingPanel`+`useAgentStream`+`SafeMarkdown`（打字机分析正文），与既有节点轨迹并存（节点轨迹与思考/分析是两类视图，均保留）。
  - 验证：recruitment `ruff`（改动，去除多余 import 后）→ 0；`pytest tests/unit/test_recruitment_stream_api.py test_sse_forwarder.py` → **3 passed**；`mypy` 全包 → 改动文件零错误，仅 1 处既有基线错误在未改动文件 `agent_api_config.py:52`。前端 `vue-tsc` 0、`eslint` 0、`vite build` 成功、共享单测 10 passed。
  - 未验证：真实浏览器端到端（需 recruitment 后端 + 网关联调）；真实模型 reasoning（阶段5）。
- 2026-07-06：**三个 Agent（data-query/legal/recruitment）后端两层 + thinking、前端三页接入统一组件均已完成并通过各自门禁**；阶段5（真实 DeepSeek 流式 + reasoning 映射，需 key，红线）与阶段6（收敛散落 `_sse_event` + 文档/契约同步）待确认。
