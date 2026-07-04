# 规则索引

本目录是唯一共享规则源，只做索引。

## 路径说明

- 若模板安装在项目根目录，路径直接使用 `.ai-rules/` 和 `skills/`。
- 若模板安装在 `.ai-spec/`，所有路径以 `.ai-spec/` 为前缀。
- `AI双工具全栈开发操作手册.md` 位于模板根目录，给用户查看，普通 AI 任务不要默认读取。

## 文件索引

- `redlines.md`：不可突破红线。
- `task-routing.md`：判断任务等级和选择 skill。
- `context-loading.md`：决定最小读取范围。
- `development-standards.md`：禁止硬编码、框架规范、跨仓边界和强制质量门禁。
- `documentation-policy.md`：什么时候更新文档。
- `git-workflow.md`：Git 分支、提交、MR/PR 和分仓提交规范。
- `modularity-output.md`：模块化代码、模块化文档和模块化交付输出规范。
- `skill-contract.md`：所有 skill 共用执行契约。
- `project-facts.example.md`：项目事实模板；真实项目可生成 `project-facts.md`，其中 `[auto]` 可刷新，`[manual]` 可由 AI 按来源填写并等待用户确认。
- `docs/rules/business-rules.example.md`：可选业务规则模板，用来源、可信度和冲突记录防止规则漂移。
- `scripts/refresh-project-facts.ps1` / `.sh`：刷新 `project-facts.md` 的 `[auto]` 段。
- `scripts/check.ps1` / `.sh`：检查模板结构、skill 契约和大小预算。
- `scripts/git-preflight.ps1` / `.sh`：提交前扫描变更文件中的密钥、真实 `.env`、超大文件和构建产物路径。

## 读取顺序

1. 先读 `task-routing.md`。
2. 再读 `context-loading.md`。
3. 命中风险时读 `redlines.md`。
4. 按任务类型读取 0-2 个相关 `skills/*/SKILL.md`。
5. 最后读取必要项目文件。

不要默认全量读取 `.ai-rules/`、`skills/`、`docs/`。

## 按需读取

- 涉及 Git、提交、分支、MR/PR 时读取 `git-workflow.md`。
- 涉及新增模块、多文件实现、重构、报告输出结构时读取 `modularity-output.md`。
- 启动或接管任务时，运行 `scripts/refresh-project-facts.ps1`（Windows）或 `scripts/refresh-project-facts.sh`（macOS/Linux）检查并刷新 `project-facts.md`；脚本只刷新 `[auto]` 段，hash 未变化时不会写入。
- 涉及业务规则、领域术语、规则冲突或验收口径时，可参考 `docs/rules/business-rules.example.md` 创建项目内业务规则文件。
- 提交或推送前，运行 `scripts/git-preflight.ps1` 或 `scripts/git-preflight.sh`；脚本只扫描当前 Git 变更，不替代人工 review。
- 用户询问双工具协作、全栈流程、Handoff 时读取模板根目录 `AI双工具全栈开发操作手册.md`。
- 普通开发任务不要默认读取操作手册。
