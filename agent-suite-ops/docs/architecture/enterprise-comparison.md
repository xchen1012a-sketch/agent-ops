# 当前目录与传统企业项目对比

## 结论

当前多仓位置合理，属于“工作区协调目录 + 独立产品仓库”模式。`agents/` 只是三个后端仓库的收纳目录，不是Git仓库；前端和运维独立放在根层，职责清楚。父目录同时保存课件和非Git计划，适合本次实训协调，但不作为发布单元。

## 对比

| 企业常见做法 | 当前项目 | 评价/补强 |
|---|---|---|
| 前端、后端、运维可独立版本 | 5个独立Git仓库 | 合理 |
| 同类微服务集中在services/ | 三个Agent集中在agents/ | 合理，名称更贴合业务 |
| 父工作区不提交子仓 | 父目录无Git | 合理，符合用户约束 |
| 计划/ADR/契约可追溯 | 计划非Git，规格/ADR在各仓 | 计划非Git是用户明确例外；架构真源仍版本化 |
| 后端src layout和测试分层 | 尚未创建 | DESIGN-002确认后由FOUND-010创建 |
| 迁移、配置、容器和CI | 尚未创建 | 当前禁止编码，后续按模块计划创建 |
| API契约驱动前后端 | 已有资源草案，Schema未冻结 | DESIGN-002必须补齐 |
| 独立数据库权限域 | 已规划四个权限域 | 必须在OPS/DATA阶段验证 |

## 目标工作区

```text
agent/
├─ agents/
│  ├─ legal-consulting-agent/      # FastAPI Agent后端仓库
│  ├─ recruitment-assistant-agent/ # FastAPI Agent后端仓库
│  └─ data-query-agent/            # FastAPI Agent后端仓库
├─ agent-suite-web/                # Vue 3前端仓库
├─ agent-suite-ops/                # 部署/标准/ADR/Runbook仓库
├─ docs/plans/                     # 用户指定的非Git计划区
└─ AI编程_智能问数实训(课件)/       # 只读需求来源
```

课件目录不得混入任何子仓构建上下文或镜像。

