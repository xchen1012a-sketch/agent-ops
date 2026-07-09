# ADR-0007：统一认证与身份边界

- 状态：已确认
- 日期：2026-07-04
- 阶段：DESIGN-002

## 背景

原计划未明确五个模块之间的身份边界。三个 Agent API、统一前端和飞书入口都需要识别用户、区分管理员与普通用户、控制菜单与 API 权限。若各 Agent 维护独立账户体系，会造成登录态割裂、用户表冗余、跨模块审计困难。

## 决策

- 认证方式：JWT，access token 15 分钟 + refresh token 7 天；refresh 存 HTTP-only Secure Cookie（前端域），access 由前端内存或 sessionStorage 持有。
- 密码哈希：BCrypt（cost=12），启动时自检；密码策略至少 8 位 + 大小写 + 数字。
- 用户表归属：`agent-suite-web` 维护统一用户表，三 Agent 信任 JWT claim 中的 `user_id` 与 `role`，不再维护独立账户体系。
- 角色模型：RBAC，`admin` / `user` 两角色；菜单可见性与 API 权限由角色决定。
- 飞书身份：飞书 `open_id` 首次消息时自动绑定到统一用户表，默认角色 `user`、无密码；飞书用户可访问 Web 端，登录态通过 open_id 换 JWT。
- 速率限制：登录 5 次/分钟/IP，全 API 60 次/分钟/用户；超限返回 429。
- Token 失效：refresh token 支持服务端撤销（黑名单或版本号字段）；密码修改后强制失效所有 refresh token。

## 后果

- 三 Agent 不再拥有独立 `/login` 接口，只暴露 `/me`、`/refresh` 之类的会话校验接口（可选）。
- 跨 Agent 用户审计通过统一 `user_id` 关联。
- 前端必须实现登录、刷新、登出与 401/403 拦截。
- 飞书适配层必须实现 open_id → JWT 的交换协议。
- JWT 签名密钥通过环境变量注入，启动时校验。

## 关键实现约束

- 密钥、Token TTL、限流阈值通过类型化 Settings 注入，不得硬编码。
- JWT claim 至少包含 `sub`（user_id）、`role`、`iat`、`exp`、`jti`。
- 失败响应统一为 401（未登录）/ 403（权限不足）/ 429（限流），不泄露用户存在性。

## 回滚

若统一认证成为阻塞（例如某 Agent 需要独立账户体系），可回退到各 Agent 自维护用户表，但必须保持 API 契约中 `user_id` 与 `role` 字段不变。
