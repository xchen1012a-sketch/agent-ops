# CONFIG-USER-001 用户级 API 配置中心

## 目标

把现有三 Agent 的 API 配置中心从全局 admin 配置改为登录账号自己的配置。用户在系统配置页填写的 API key 只归属本人，后端按当前请求的 `x-user-public-id` 隔离读写。

## 范围

- 三个 Agent 的 `agent_api_config` 模型、实体、repository 和配置接口。
- 三个 Agent 新增最小 Alembic 迁移，创建用户级配置表。
- 统一 Web 的 API 配置页面和 API client 路径。

## 不做事项

- 不接真实 DeepSeek 调用链。
- 不实现管理员代管其它用户配置。
- 不修改全局认证体系。
- 不提交或写入真实 API key。

## 验收

- 普通登录用户可访问配置页。
- 后端按当前用户列出、读取、更新自己的配置。
- 数据库唯一约束为 `user_public_id + api_type`。
- 至少覆盖一个允许路径和一个跨用户隔离路径的测试。

## 执行记录

- 待执行。
