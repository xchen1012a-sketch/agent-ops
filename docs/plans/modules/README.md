# 模块详细计划索引

本目录是父协调目录的非 Git 计划区。模块真源规格位于各自 Git 仓库，实施计划不得反向修改真源需求。

| 模块 | 仓库 | 真源规格 | 详细计划 | 计划完整性 | 开发状态 |
|---|---|---|---|---|---|
| 统一前端 | `agent-suite-web` | `agent-suite-web/docs/specification.md` | `agent-suite-web.md` | 已补齐 | 等待 DESIGN-002 对齐 |
| 法律咨询 Agent | `agents/legal-consulting-agent` | `docs/specification.md` | `legal-consulting-agent.md` | 已补齐 | 等待 DESIGN-002 对齐 |
| 智能招聘 Agent | `agents/recruitment-assistant-agent` | `docs/specification.md` | `recruitment-assistant-agent.md` | 已补齐 | 等待 DESIGN-002 对齐 |
| 智能问数 Agent | `agents/data-query-agent` | `docs/specification.md` | `data-query-agent.md` | 已补齐 | 等待 DESIGN-002 对齐 |
| 运维协调 | `agent-suite-ops` | 架构、ADR、契约与 Runbook | `agent-suite-ops.md` | 已补齐 | 等待 DESIGN-002 对齐 |

## 执行规则

1. 总体 `current.md` 一次只允许指向一个阶段。
2. 开始模块子阶段前，在 `docs/plans/phases/` 建立对应阶段文件。
3. 未完成 DESIGN-002 的未决问题清零和用户确认，任何模块不得编码。
4. 每阶段只修改计划列出的仓库和文件类型；扩大范围先更新计划并等待确认。
5. 验收证据必须来自实际命令、测试、截图或可复现运行记录。
6. 不执行未验证却标记通过，不自动提交或推送 Git。

