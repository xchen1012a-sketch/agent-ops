# ADR-0001：采用五仓多仓架构

- 状态：已由 ADR-0006 取代
- 日期：2026-07-04

## 背景

用户要求统一前端、三个独立 Agent 后端、一个运维协调仓库，并要求各项目独立 Git、独立部署和互不耦合。

## 决策

采用五个 Git 仓库：`agent-suite-web`、`agents/legal-consulting-agent`、`agents/recruitment-assistant-agent`、`agents/data-query-agent`、`agent-suite-ops`。三个 Agent 统一收纳在 `agents/`，其容器目录本身不初始化 Git。父目录不初始化 Git；总体计划位于父目录 `docs/plans/`。

## 后果

- 仓库可独立发布和回滚。
- 跨仓变更必须依赖版本化 API 契约，不能依赖同步提交。
- 公共规范允许复制模板，但不建立共享业务运行库。
- 运维仓必须明确兼容的镜像版本。

## 回滚

若未来改为单仓，必须先冻结所有仓库版本、迁移 Git 历史并更新 API/部署契约；不得直接把子仓 `.git` 删除后合并。
