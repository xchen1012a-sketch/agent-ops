# 部署拓扑设计

## 独立部署

每个 Agent 镜像仅包含所属仓库产物，配置自身 DeepSeek 和 MySQL 连接，可独立启动并通过 `/health/live`、`/health/ready` 验证。

## 统一编排

`agent-suite-ops` 后续统一编排：

- Web 静态服务/反向代理
- 三个 Agent API
- MySQL 8 开发实例及三个独立账号
- 可选可观测组件

统一编排必须引用镜像版本，不跨仓挂载源码。每个 Agent 的单独 Compose 由其仓库负责，跨仓 Compose 由本仓库负责。

## 配置层级

1. 非敏感默认值：仓库 `.env.example`。
2. 环境差异：部署环境变量。
3. 密钥：本地未跟踪 `.env` 或部署平台 Secret。
4. 禁止把真实配置复制到文档、截图或 Git。

当前文档只定义拓扑，不执行部署。

