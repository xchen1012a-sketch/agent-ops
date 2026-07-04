# FOUND-010 企业级工程基础

## 状态

待 DESIGN-002 完成并经用户明确允许开发后开始。本文件是预先准备的执行计划，不代表已进入编码。

## 目标

按照已确认企业标准，为三个FastAPI Agent、统一Vue前端和运维仓建立最小可运行、可测试、可迁移、可容器化的工程基础，并完成一个不含真实业务的健康检查垂直切片。

## 范围

- 三个Agent：src layout、FastAPI应用壳、LangGraph装配入口、Settings、错误、日志、live/ready、SQLAlchemy/Alembic、测试和Docker基础。
- 前端：Vite/Vue3/TypeScript/Element Plus应用壳、路由、配置、错误边界和测试基础。
- 运维：服务命名、镜像规范、非敏感环境模板和独立启动验证。
- 质量：lint、format、type、unit、contract、migration、build和安全扫描命令。

## 不做事项

- 不实现法律、招聘、智能问数业务功能。
- 不连接真实DeepSeek、飞书或生产MySQL。
- 不创建共享业务运行库或跨仓源码依赖。
- 不硬编码地址、密钥、端口、模型或数据库。

## 影响仓库

- `agent-suite-web`
- `agents/legal-consulting-agent`
- `agents/recruitment-assistant-agent`
- `agents/data-query-agent`
- `agent-suite-ops`

每个仓库分别修改、分别验证；不得在父目录提交。

## 分阶段执行

1. 固化兼容版本矩阵和许可证检查。
2. 建立三个后端同构骨架，但分别拥有独立包名、配置和测试；仅提供LangGraph factory扩展点，不默认安装Deep Agents。
3. 建立前端应用壳和契约Mock基础。
4. 建立迁移基线与四数据库权限设计，不创建业务表。
5. 建立Docker和健康检查，不统一编排业务依赖。
6. 执行全部工程门禁并记录证据。

## 验收标准

- 每个Agent能独立启动并生成OpenAPI；live/ready语义正确。
- 三个Agent没有互相import或共享运行包。
- AsyncSession按请求/任务隔离；迁移升级/回滚空库通过。
- 前端lint、typecheck、unit和production build通过。
- 每仓Docker镜像以非root运行并有健康检查。
- `.env.example`无真实秘密，关键配置缺失时快速失败。
- 项目规则、禁止硬编码扫描和依赖/许可证检查通过。

## 停止条件

- DESIGN-002未完成或用户未允许开发。
- 框架版本不兼容、许可证不明确或需要废弃API。
- 需要提前实现业务才能让骨架运行。
- 需要修改仓库边界、API主版本、数据库权限或认证架构。

## 回滚

各仓独立回滚本阶段新增骨架文件；迁移基线使用downgrade验证；不删除规格、ADR和计划。未获得用户授权不执行Git提交或推送。
