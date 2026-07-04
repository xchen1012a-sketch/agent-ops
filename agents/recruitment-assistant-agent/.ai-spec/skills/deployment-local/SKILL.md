---
name: deployment-local
description: 管理本地启动、端口、健康检查和开发环境脚本。用于 start/check/stop/smoke、docker-compose、服务 URL、PowerShell 注意事项和本地依赖边界。
---

# Deployment Local

## 目标

让本地环境可重复启动、可检查、可停止。不要靠一次性临时命令堆出“刚好能跑”的状态。

## 适用场景

- 本地启动前端、后端、worker。
- 端口占用、health check、ready check。
- docker-compose、本地 Redis/PostgreSQL。
- 规范化 start/check/test/smoke 脚本。

## 不适用场景

- 生产部署。
- 云服务发布。
- 需要真实生产数据库或付费外部服务的操作。

## 最小上下文

1. `scripts/`。
2. README 或开发启动说明。
3. package/pyproject/compose/env example。
4. health/ready endpoint。
5. 当前端口占用信息，只有需要启动时读取。

## 工作流

1. 优先找项目已有 start/check/stop/smoke 脚本。
2. 没有脚本时补模板脚本，不把一长串临时命令只留在聊天里。
3. 启动前确认依赖：Node/Python、环境变量、数据库、Redis、端口。
4. 端口占用先查明进程，不盲目 kill。
5. Windows PowerShell 注意执行策略、路径空格、后台进程、编码。
6. 服务启动后必须 health/ready check。
7. 记录服务 URL、端口、进程或日志位置。
8. 真实 Redis/PostgreSQL/外部 AI 服务接入前暂停确认。
9. 长期后台服务需要用户明确允许。

## 脚本职责

- `scripts/check.*`：静态检查、环境检查、配置检查。
- `scripts/test.*`：项目测试入口。
- `scripts/smoke.*`：服务健康检查、主 API、主页面。

## 文件边界

- `scripts/start.*` 只负责启动本地服务；不得顺手安装依赖、迁移生产库或写全局配置。
- `scripts/stop.*` 只停止明确属于当前项目的进程；不得按端口盲杀未知进程。
- `scripts/check.*` 只检查环境、配置和必要文件；不得修改业务代码。
- `scripts/smoke.*` 只做健康检查和最小主路径验证；不得创建不可恢复数据。
- `docker-compose.*` 只描述本地依赖；真实生产服务不得作为默认依赖。
- `.env.example` 只放变量名和安全示例；真实 `.env` 不提交、不输出。
- 日志文件路径要固定到项目内 `logs/` 或临时目录，并在输出中说明。

## 验证清单

- [ ] 使用或创建了标准脚本入口。
- [ ] 服务 URL 已记录。
- [ ] health/ready 已检查。
- [ ] 端口占用已说明。
- [ ] 没有连接未确认的真实外部服务。
- [ ] 没有留下未知后台进程。

## 输出要求

说明使用的脚本、服务 URL、健康检查结果、端口/进程状态、未启动项、需要用户确认的依赖。
## 停止条件

- 需要终止未知进程、占用端口进程或系统服务但用户未确认。
- 需要安装依赖、修改系统环境变量、防火墙、代理或全局配置。
- 服务启动依赖真实外部资源但当前没有明确 mock 或本地替代。
- 健康检查失败且日志不足以判断原因。
## 强制执行规则

- 遵守 `.ai-rules/skill-contract.md`。
- 本 skill 的工作流、停止条件和验证方式优先于通用建议。


