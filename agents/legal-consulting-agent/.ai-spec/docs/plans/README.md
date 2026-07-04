# plans

模板目录里的 `docs/plans` 只提供示例，不记录真实项目状态。

## 真实计划写在哪里

- 单子仓任务：写到该子仓的 `docs/plans/`。
- 跨仓任务：父目录 `docs/plans/` 写总协调计划；各子仓 `docs/plans/` 写各自阶段和验收。
- 规则模板维护：只更新模板示例，不写具体项目事实。

## 使用规则

- 小任务不需要计划。
- `current.md` 是当前阶段入口。
- `project-plan.md` 是总计划，只在范围变化、架构变化、阶段变化时维护。
- 新项目、旧项目接入、架构调整、多子仓协作必须先有总计划和分阶段执行计划。
- 用户确认计划并说“执行”后，先写入 `project-plan.md`、`current.md` 和 `phases/*.md`，再开始第一阶段实现。
- 执行时只做 `current.md` 指向的当前阶段，不同时推进多个阶段。
- 阶段完成必须记录验证证据。

## 修复和 Review 计划

建议路径：

```text
docs/plans/phases/FIX-<short-name>.md
docs/plans/phases/REV-<short-name>.md
```

具体触发条件和字段要求见 `.ai-rules/task-routing.md`；这里不重复维护。

## 建议结构

```text
docs/plans/
├── current.md
├── project-plan.md
├── bugfix-review-plan.example.md
└── phases/
    ├── FE-01-frontend-mvp-ui.md
    ├── FIX-login-timeout.md
    ├── REV-auth-boundary.md
    └── BE-01-api-baseline.md
```
