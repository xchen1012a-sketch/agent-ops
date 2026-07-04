# agent-lite-rules

项目级「轻规则 + 强 Skills」模板，面向 Claude Code 和 Codex。

仓库：`https://github.com/xchen1012a-sketch/agent-lite-rules`

## 1. 核心

把 AI 协作规则放进当前项目，让 AI 先按项目规则、项目事实和项目 skills 工作，再按需补充全局能力。

- 项目优先：全局 rules 只能做背景，不能覆盖当前项目 `.ai-spec/`。
- 少读上下文：不默认全量读取 `.ai-spec/`、`skills/`、`docs/`。
- 简洁实现：能用小改解决，不写大框架；不做未要求的扩展。
- 事实分层：`project-facts.md` 的 `[auto]` 由脚本刷新，`[manual]` 由 AI 按来源填写、用户确认。
- 分阶段执行：L2+ bugfix / review-fix 先写 Markdown 阶段计划。
- 不碰全局：不写用户全局 Claude / Codex 配置、rules、skills、hooks、MCP。

## 2. 目录

推荐安装到目标项目的 `.ai-spec/`：

```text
项目根目录/
├── CLAUDE.md
├── AGENTS.md
└── .ai-spec/
    ├── .ai-rules/     # 任务路由、上下文、红线、Git、输出规则
    ├── skills/        # 项目优先 skills
    ├── docs/          # 计划、契约、验收示例
    └── scripts/       # 接入和检查脚本
```

## 3. 接入

在目标项目根目录执行。

macOS / Linux：

```bash
git clone https://github.com/xchen1012a-sketch/agent-lite-rules.git .ai-spec && bash .ai-spec/scripts/create-entry.sh && bash .ai-spec/scripts/refresh-project-facts.sh
```

Windows：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "git clone https://github.com/xchen1012a-sketch/agent-lite-rules.git .ai-spec; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; & .\.ai-spec\scripts\create-entry.ps1; & .\.ai-spec\scripts\refresh-project-facts.ps1"
```

脚本不会覆盖已有入口文件；冲突时生成 `.proposed`。

## 4. AI 启动

1. 读项目根目录 `CLAUDE.md` 或 `AGENTS.md`。
2. 读 `.ai-spec/.ai-rules/README.md`。
3. 读 `.ai-spec/.ai-rules/task-routing.md`。
4. 读 `.ai-spec/.ai-rules/context-loading.md`。
5. 运行 `.ai-spec/scripts/refresh-project-facts.ps1` 或 `.ai-spec/scripts/refresh-project-facts.sh` 检查并刷新 `[auto]` 项目事实。
6. 按任务只读 0-2 个相关 `skills/*/SKILL.md`。
7. 命中安全、权限、外部服务、全局配置时，再读 `redlines.md`。

L2+ 任务最终必须说明读取了哪些项目 rules / skills；命中项目 skill 但读取数量为 0 时必须重新路由。

## 5. 常用命令

刷新项目事实：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .ai-spec\scripts\refresh-project-facts.ps1
```

```bash
bash .ai-spec/scripts/refresh-project-facts.sh
```

检查模板：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .ai-spec\scripts\check.ps1
```

```bash
bash .ai-spec/scripts/check.sh
```

提交前扫描：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .ai-spec\scripts\git-preflight.ps1
```

```bash
bash .ai-spec/scripts/git-preflight.sh
```

更新模板：

```bash
git -C .ai-spec status --short
git -C .ai-spec pull --ff-only
```

## 6. 使用提示

- 新项目：先做计划，确认后再生成计划文件和项目结构。
- 已有项目：先只读盘点；确认前不改业务代码、不初始化 Git、不安装依赖、不启动服务。
- L2+ bugfix / review-fix：先写 `docs/plans/phases/FIX-*.md` 或 `REV-*.md`，再分阶段修复和验证。
- 提交或推送前运行 `git-preflight.ps1` / `git-preflight.sh`；它只扫当前 Git 变更。
- `project-facts.md`：`[auto]` 由脚本刷新；`[manual]` 可由 AI 填写，但必须带来源/状态，未知项留空或标待确认。
- 业务规则可选落到 `docs/rules/business-rules.md`，只记录有来源的规则、术语和冲突。

## 7. 常用提示词

空项目先做计划：

```text
我想做一个新项目，想法是：【写你的项目想法】。
请先不要创建文件、不要初始化 Git、不要安装依赖、不要写代码。
请先按 .ai-spec 规则判断任务等级，读取必要项目 rules/skills。
输出项目计划草案：项目名、业务域、模块词表、仓库结构、阶段前缀、阶段列表、第一阶段验收标准和需要我确认的问题。
等我确认并说“执行”后，再生成计划文件和项目结构。
```

已有项目接入：

```text
请使用 .ai-spec 接入当前已有项目。
先只读盘点目录结构、技术栈、已有 AI 规则、docs/plans、scripts、Git 状态和关键入口文件，并运行 project-facts 刷新脚本只生成/更新 [auto] 段。
不要创建业务文件、不要初始化 Git、不要安装依赖、不要启动服务、不要修改业务代码、不要覆盖已有文件。
请输出接管报告：项目事实、规则冲突、单仓/多仓判断、建议接入位置、风险和需要我确认的问题。
```

执行当前阶段：

```text
我确认计划，可以开始执行当前阶段。
请先刷新 project-facts [auto] 段，再读取 docs/plans/current.md 和它指向的 phase，只执行当前阶段。
执行前报告任务等级、读取的项目 rules/skills、目标、范围、不做事项、验收标准和计划修改文件。
遇到计划外文件先报告，不要同时推进多个阶段。
```

Review / bugfix 分阶段修复：

```text
请先 review / 复现问题，不要直接改代码。
请按 project-first 读取项目 rules/skills，并说明读取了哪些项目 rules/skills。
如果达到 L2 及以上，先生成 docs/plans/phases/FIX-*.md 或 REV-*.md，写清问题、证据、影响范围、不做事项、阶段步骤、验证方式、停止条件和回滚方式。
等阶段计划明确后，只执行第一阶段修复；每阶段完成后写回验证证据。
```

更新模板 / 同步规则：

```text
.ai-spec 模板已更新，请先只读检查当前项目是否需要同步。
对比项目根目录 CLAUDE.md、AGENTS.md、.ai-spec/.ai-rules/、.ai-spec/skills/、.ai-spec/scripts/。
不要覆盖文件、不要修改业务代码、不要安装依赖、不要启动服务；如需更新，生成 .proposed 或输出差异清单。
请输出同步建议、风险、需要我确认的问题，以及确认后要替换的文件列表。
```

## 8. 边界

允许写当前项目：

- `CLAUDE.md`
- `AGENTS.md`
- `.ai-spec/`
- 已确认需要的 `docs/`、`scripts/`

禁止写或改：

- `~/.claude/`
- `~/.codex/`
- 全局 rules、skills、hooks、MCP
- 未确认的业务代码、生产配置、密钥文件
