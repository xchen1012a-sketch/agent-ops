# FEISHU-300 飞书 Webhook 配置接通与服务器部署

## 状态

- 阶段：计划已写，待用户确认后开始 Phase A。
- 上一阶段：`FIX-agent-ui-claude-alignment`（已完成）。
- 上一飞书阶段：`agents/data-query-agent/docs/plans/phases/FEISHU-100-bot-integration.md`（FEISHU-100/200 完成，FEISHU-300 部署未做）。
- 当前 `docs/plans/current.md` 指向待更新为本阶段。

## 目标

让用户在统一 Web 工作台的「API 配置」页填入飞书 4 个字段（App ID / App Secret / Verification Token / Encrypt Key）后，data-query-agent 的 `/integrations/feishu/webhook` 端点自动启用，飞书机器人可端到端响应（@机器人 或私聊 → 触发问数工作流 → 文本回推）。同时把整套系统部署到用户已有的阿里云 ECS（带域名 + SSL）。

满足《大数据应用实训》第四章「智能问数系统实战」对飞书入口证据的硬要求。

## 现象 / 问题

- 真实 webhook 端点 `api/v1/endpoints/feishu_webhook.py` 已实现并注册到路由，但被 `settings.feishu_enabled=false` 默认关闭。
- 4 个飞书凭证目前从环境变量读（`core/config.py:103-108`），未接 API 配置中心。
- 前端 `ApiConfigEditor.vue` 对所有 api_type 渲染同一套单 key 表单，无法录入 4 字段。
- 用户期望「页面填字段 → 直接生效」而非「改服务器 env → 重启」。

## 证据

| 现状 | 文件 / 行号 |
|---|---|
| 真端点已注册 | `api/v1/router.py:23` |
| 真端点实现 | `api/v1/endpoints/feishu_webhook.py:21-41` |
| Deps 装配从 env 读 | `api/dependencies.py:162-181 get_feishu_webhook_deps` |
| Settings 4 字段 | `core/config.py:103-111` |
| 启用校验硬约束 | `core/config.py:142-148` |
| `extra` 列已存在 | `domain/entities/agent_api_config.py:29`、`infrastructure/db/repositories/agent_api_config.py:52` |
| 前端表单单一 key | `agent-suite-web/src/components/admin/ApiConfigEditor.vue:79-88` |
| 现有单测覆盖 | `tests/unit/test_feishu_webhook.py`、`tests/unit/test_config.py:102-115` |

## 影响范围（核查后）

### 必改（6 个文件）

| # | 文件 | 改什么 |
|---|---|---|
| 1 | `agents/data-query-agent/src/data_query_agent/api/dependencies.py` | `get_feishu_webhook_deps` 改为读 DB；加 60s TTL 缓存 |
| 2 | `agents/data-query-agent/src/data_query_agent/infrastructure/db/repositories/agent_api_config.py` | 新增 `get_enabled_feishu_config()` 方法 |
| 3 | `agents/data-query-agent/src/data_query_agent/core/config.py` | 移除 `validate_required` 对 `feishu_*` 的硬校验；保留字段作为应急 kill switch |
| 4 | `agents/data-query-agent/.env.example` | 删 4 个 `FEISHU_*` 行，改注释说明 |
| 5 | `agents/data-query-agent/tests/unit/test_config.py` | 移除 / 调整 feishu 校验断言 |
| 6 | `agents/data-query-agent/tests/unit/test_feishu_webhook.py` | 增 DB mock fixture；保留现有 5 个 processor 用例不动 |

### 必改前端（2 个文件）

| # | 文件 | 改什么 |
|---|---|---|
| 7 | `agent-suite-web/src/components/admin/ApiConfigEditor.vue` | `api_type==='feishu'` 时渲染 4 字段表单（App ID / App Secret / Verification Token / Encrypt Key） |
| 8 | `agent-suite-web/src/api/admin-api-config.ts` | 飞书行 save/load 时 4 字段 ↔ `extra` JSON 互转 |

### 部署新增（3 个文件）

| # | 文件 | 内容 |
|---|---|---|
| 9 | `agent-suite-ops/nginx/suite.conf`（新建） | 域名 + SSL 反代 → web/5173、data/8103、legal/8101、recruit/8102 |
| 10 | `agent-suite-ops/docker-compose.yml` | 取消注释 `suite-web` 与 `suite-ops-nginx` 服务 |
| 11 | `agent-suite-ops/.env`（用户服务器上填，不入 Git） | 真实 MYSQL/JWT/DEEPSEEK 密钥 |

### 不动（边界守护）

- `agents/legal-consulting-agent/**`、`agents/recruitment-assistant-agent/**`：无飞书代码，零改动。
- `agents/auth-service/**`：与飞书无关，零改动。
- `feishu_events.py`、`feishu_webhook_service.py`、`feishu_bot_service.py`、`feishu_client.py`、`feishu_signature.py`、`feishu_event_dedup.py`：业务实现稳定，不动。
- 其它 api_type（deepseek/mcp/embedding/vector_db/reranker/ocr）的存储与表单分支不动。
- 现有 mock 端点 `feishu_events.py` 保留作离线测试入口。

## 关键设计决策

### 1. 多用户配置冲突 → 「最新启用行」策略

webhook 是飞书回调，无 `X-User-Subject` 头，无法识别用户。`agent_api_config` 表是 per-user 的。冲突解法：

**采用方案 A**：webhook 装配时查 `agent_api_config WHERE api_type='feishu' AND enabled=true ORDER BY updated_at DESC LIMIT 1`。

- 单 admin 用户演示场景下，per-user == system，无歧义。
- 多用户都配的话「最后写的赢」，UI 提示文案说明此规则。
- 不新增 `system_api_config` 表（方案 B，过度工程）。
- 不保留 env 兜底（方案 C，违背目标）。

### 2. 4 字段存储映射（不改表结构）

`agent_api_config.api_key_encrypted` 已有 Fernet 加密列；`extra` 已有 JSON 列。

| 飞书字段 | 列 | 加密 | 理由 |
|---|---|---|---|
| `app_secret` | `api_key_encrypted` + `api_key_hint` | ✅ Fernet | 最敏感，必须加密 |
| `app_id` | `extra.app_id` | ❌ 明文 | 半公开标识，飞书后台可见 |
| `verification_token` | `extra.verification_token` | ❌ 明文 | 防伪字符串，演示场景接受 |
| `encrypt_key` | `extra.encrypt_key` | ❌ 明文 | AES 密钥；MVP 妥协，写入风险章节 |

**已知局限**：encrypt_key 明文存储意味着有 DB 读权限的人可解密历史 webhook 调用。本作业演示数据非生产数据，可接受。后续如需收紧，加 `extra_encrypted` 列是独立工作项，不在本阶段。

### 3. 启用开关保留为应急 kill switch

`settings.feishu_enabled`（env `FEISHU_ENABLED`）保留，**默认 `false`**：

- 默认 false 保证现有 `test_route_returns_404_when_feishu_disabled` 测试不动。
- 部署到服务器时设为 true，作为全局总开关。
- DB 有 enabled 行 + `feishu_enabled=true` 双条件才生效。
- 紧急下线：ops 改 env 重启即可，无需 DB 访问。

### 4. 60 秒 TTL 缓存

webhook 调用频率不高（每条飞书消息一次），但每次查 DB + Fernet 解密有成本。加进程内 TTL 缓存：

- key 固定（全局单例 feishu 配置）
- TTL 60s
- 配置更新接口触发 invalidate（best-effort）

## 不做事项

- 不实现飞书长连接 / WebSocket 模式（用户已确认走 webhook）。
- 不接 OCR、不导入法律知识库、不部署 Qdrant/BGE。
- 不动 DeepSeek 配置链路（独立工作项，可后续做）。
- 不实现飞书交互卡片 / 流式卡片 / 多群聊 / 图片消息。
- 不修改三个 Agent 之间的隔离边界。
- 不引入新依赖（不加 `lark-oapi`）。

## 分阶段实施

### Phase A：后端 — DB 读取与缓存（data-query-agent）

范围：
1. `agent_api_config.py` 仓库新增 `get_enabled_feishu_config()` 异步方法，返回最新启用行或 None。
2. `api/dependencies.py` 新增 `_FeishuConfigCache` 进程级缓存（TTL 60s），缓存解密后的 4 字段。
3. `get_feishu_webhook_deps` 改为：
   - `settings.feishu_enabled=false` → 返回 disabled（保留原行为）
   - 否则查缓存 / DB → 取不到 enabled 行 → 返回 disabled
   - 取到 → 用 DB 字段构造 `FeishuWebhookProcessor` 与 `FeishuClient`
4. `core/config.py:142-148` 移除对 `feishu_app_id/app_secret/verification_token` 的硬校验。
5. `.env.example` 删 4 行 `FEISHU_*`，改为说明性注释。

验证：
- `ruff check agents/data-query-agent/src`
- `mypy agents/data-query-agent/src`
- `pytest agents/data-query-agent/tests/unit/test_feishu_webhook.py`（新增 DB mock fixture）
- `pytest agents/data-query-agent/tests/unit/test_config.py`（更新断言）
- 现有 6 个 feishu 相关单测全绿

停止条件：以上 4 项任一失败立即停下排查，不进入 Phase B。

### Phase B：前端 — 4 字段表单（agent-suite-web）

范围：
1. `ApiConfigEditor.vue`：`api_type==='feishu'` 时切换为 4 输入框（App ID / App Secret / Verification Token / Encrypt Key），其余 api_type 沿用单 key 表单。
2. `admin-api-config.ts`：
   - save 时把 4 字段拼成 `extra: {app_id, verification_token, encrypt_key}` + `api_key: app_secret`
   - load 时从 `extra` + `api_key_hint` 还原表单
3. 飞书行额外显示「Webhook URL」只读提示：`https://{域名}/api/data/v1/integrations/feishu/webhook`，方便用户复制到飞书后台。

验证：
- `pnpm typecheck`
- `pnpm lint`
- 浏览器手测：进入 API 配置 → 切到 data tab → 编辑飞书行 → 看到 4 字段表单 → 保存成功 → 刷新仍可见
- 浏览器手测：deepseek/mcp 行的表单不受影响

停止条件：typecheck / lint 任一失败；4 字段保存后刷新丢失；其它 api_type 表单异常。

### Phase C：阿里云部署

前置条件：用户提供 ECS SSH 访问、域名 DNS 控制权、SSL 证书文件（或 Let's Encrypt 路径）。

范围：
1. ECS 安装 Docker + docker compose 插件。
2. `git clone` 项目到 `/opt/enterprise-agent-suite`。
3. `agent-suite-ops/.env` 填入真实值（MYSQL_ROOT_PASSWORD / JWT_SECRET / DEEPSEEK_API_KEY / FEISHU_ENABLED=true 等）。
4. `agent-suite-ops/nginx/suite.conf` 新建：
   - 80 端口 redirect → 443
   - 443 SSL + 反代 `/` → suite-web:5173
   - 反代 `/api/legal/` → legal-agent:8101
   - 反代 `/api/recruitment/` → recruitment-agent:8102
   - 反代 `/api/data/` → data-query-agent:8103
   - SSE 长连接配置（`proxy_buffering off`、`proxy_read_timeout 600s`）
5. `docker-compose.yml` 取消注释 `suite-web` 与 `suite-ops-nginx`。
6. `docker compose up -d` 起全栈。
7. DNS A 记录指向 ECS 公网 IP。

验证：
- `curl https://{域名}/api/data/v1/health/live` 返回 200
- 浏览器打开 `https://{域名}` 看到 Web 工作台登录页
- 三个 Agent 健康检查通过

停止条件：任一容器健康检查失败；HTTPS 证书校验失败；任一 Agent 端点 5xx。

### Phase D：飞书后台配置 + 端到端联调

前置条件：用户已注册飞书开发者账号、有权限创建企业自建应用。

范围：
1. 飞书开放平台 → 创建企业自建应用 → 拿 App ID + App Secret。
2. 应用能力 → 添加「机器人」。
3. 事件订阅 → 选「事件订阅」模式（**不**选长连接）→ 填回调 URL `https://{域名}/api/data/v1/integrations/feishu/webhook`。
4. 复制 Verification Token、设置 Encrypt Key（任意 32+ 字符随机串）。
5. 订阅事件 `im.message.receive_v1`。
6. 权限管理 → 申请 `im:message`、`im:message:send_as_bot`。
7. 发布版本 → 管理员审核通过。
8. 回到我们系统 API 配置页 → 切到 data tab → 编辑飞书行 → 填 4 字段 → 启用 → 保存。
9. 飞书里私聊机器人发「上月销售额最高的 5 个品类」→ 收到工作流回推文本。

验证：
- 飞书事件订阅页「请求地址校验」通过（webhook 返回正确 challenge）。
- 飞书里发任意文本 → 1-10 秒内收到回复。
- 重复发同一条消息 → 只回复一次（去重生效）。
- 服务器日志可见 `feishu.workflow_failed=false`、`answer` 非空。

停止条件：URL 校验不通过（多为 nginx 路径或 HTTPS 问题）；权限不足；工作流抛错。

## 每阶段验证证据归档

每阶段完成后，在 `agents/data-query-agent/docs/acceptance-closeout.md` 或本文件追加：

- Phase A：ruff/mypy/pytest 输出末尾片段。
- Phase B：typecheck/lint 输出 + 浏览器截图路径。
- Phase C：`docker compose ps` 健康状态 + curl 输出。
- Phase D：飞书 URL 校验通过截图 + 端到端对话截图。

## 回滚 / 降级

| 阶段 | 回滚动作 |
|---|---|
| Phase A | `git revert`；DB schema 未变，无需迁移回滚 |
| Phase B | `git revert`；前端构建独立 |
| Phase C | `docker compose down`；保留 ECS 实例可重启旧版镜像 |
| Phase D | 飞书后台「停用应用」即可；DB 中 enabled=false 关闭集成 |

## 红线 / 安全

- 不在 Git 中提交任何真实飞书凭证、SSL 私钥、MYSQL 密码。
- `.env` 文件 `.gitignore` 已覆盖（核查 `agent-suite-ops/.gitignore`）。
- encrypt_key 明文存储的限制必须写入「REPORT-800 风险说明」。
- 飞书回调仅校验签名 + verification token，不做用户级鉴权（飞书无法带用户头），符合设计。
- webhook 端点响应不套 `{data, error}` Envelope（已有代码注释写明原因）。

## 工作量估计

| 阶段 | 内容 | 估时 |
|---|---|---|
| A | 后端 DB 接通 + 测试 | 1.5-2h |
| B | 前端 4 字段表单 + 测试 | 1-1.5h |
| C | ECS 部署 + nginx + DNS | 1-2h |
| D | 飞书后台 + 端到端 | 0.5-1h |
| **合计** | | **4-6.5h**（半天到一天） |

## 待用户确认

1. 是否同意上述 4 个关键设计决策（最新启用行 / extra 明文 / kill switch / 60s 缓存）？
2. Phase C 部署时能否提供：ECS 公网 IP、域名、SSL 证书路径（或同意用 Let's Encrypt）？
3. 是否同意 Phase A 完成后先暂停让你 review，再进入 Phase B？

确认后我会更新 `docs/plans/current.md` 指向本阶段，然后开始 Phase A 第 1 步：仓库方法 `get_enabled_feishu_config()`。
