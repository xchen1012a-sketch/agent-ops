# FEISHU-100 飞书机器人对接（data-query-agent）

## 目标
在 data-query-agent 接入一个飞书机器人：用户在飞书里 @机器人 / 私聊发文本 →
系统异步调用现有 data-query 工作流 → 把 `answer` 文本回推到同一会话。
约束：不改动 agent 内部（只调用 `create_data_query_graph().invoke({"question": ...})`）；
复用现有用户数据隔离机制（`external_subject` → `UserMirror`）。

## 决策（已与用户确认）
- 落地服务：仅 data-query-agent（另两个 agent 后续复制同一模式）。
- 单个机器人（一套 App 凭证）。
- 异步回推（先回 200，后台跑工作流，再用发消息 API 回推）。
- 回复形态：纯文本（复用 `state["answer"]`，暂不用交互卡片）。

## 数据隔离
- 飞书用户 `open_id` 映射为 `external_subject = "feishu:{open_id}"`，
  接入现有 `IdentityThreadService.get_or_create_user`，thread/message/run 全部按 `user_id` 过滤。
- 多企业时前缀再拼 `tenant_key`。

## 关键冲突/风险（已在方案阶段指出）
1. 飞书回调响应不能套内部 `{data, error}` Envelope：url_verification 要原样回 challenge，
   事件要快速回 200。仅此对外端点破例，代码注释写明原因。
2. `graph.invoke` 同步阻塞，飞书要求 3s 内响应 → 必须异步：先回 200，后台执行 + 回推。
3. 现有 mock 去重是进程内 `set()`，阿里云多 worker 会重复处理 → 生产用 Redis SETNX+TTL。
4. `tenant_access_token` 多进程共享 → Redis 缓存，避免各进程各刷触发频控。

## 分阶段

### Phase FEISHU-100（本阶段：离线安全地基，无网络、无真凭证、不改现有端点）
范围：
- `core/config.py`：新增飞书配置项；`validate_required` 在 `feishu_enabled=true` 时硬校验。
- `.env.example`：补占位配置。
- `infrastructure/integrations/feishu_signature.py`（新增）：请求签名校验 + 事件体 AES 解密 +
  verification token 校验，纯函数、可离线测试。
- `tests/unit/test_feishu_signature.py`、`tests/unit/test_config.py`：单测（含拒绝路径）。
验收：ruff + mypy + 上述两个测试文件全绿；不触碰现有 mock 端点与其测试。

### Phase FEISHU-200（代码已搭建 + 离线验证通过；启用仍需用户填真凭证）
- `infrastructure/integrations/feishu_client.py`（新增）：`FeishuHttpClient`(Protocol)+httpx 实现；
  `tenant_access_token` 获取 + Redis 缓存；`send_text(receive_id, text)` 发消息。仿 DeepSeek adapter 模式，含 fake 离线测试。
- Redis provider + lifespan 初始化。
- `infrastructure/integrations/feishu_events.py`：去重从 `set()` 换 Redis SETNX+TTL。
- `application/services/feishu_bot_service.py`（新增）：解析事件 → 映射用户 → invoke 工作流 → 发文本。
- 端点重写 `api/v1/endpoints/feishu_events.py`：验签 → url_verification → 去重 → BackgroundTasks 异步 → 快速回 200。
- `api/v1/schemas/feishu_events.py`：真实事件 DTO（加密体 / header.event_type / message.content / sender.open_id）。
- dependencies + router 接线；`.env` 真凭证由 ops 填；`FEISHU_ENABLED=true` 启用。
验收：伪 HTTP client 单测 + 本地 smoke（挑战应答、消息回推）。

### Phase FEISHU-300（部署/上线）
- nginx HTTPS 反代到 agent 端口，飞书事件订阅地址 `https://域名/api/data/v1/integrations/feishu/events`。
- 阿里云多副本下 Redis 去重/令牌缓存回归；频控与超时演练。

## 停止条件
- Phase 200 起连接真实飞书/Redis 前，必须拿到 App 凭证并经用户确认（命中 backend-api /
  security-hardening 停止条件与红线「未确认前不连外部服务」）。
