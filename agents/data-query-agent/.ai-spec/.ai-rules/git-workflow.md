# Git 提交规范

本文件只在涉及 Git、分支、提交、MR/PR、交接时读取。普通开发任务不要默认读取。

## 基本原则

- 不自动 `git add` / `git commit` / `git push`，除非用户明确要求。
- 提交前必须先看 `git status` 和相关 `git diff`。
- 只提交本次任务相关文件，不夹带无关改动。
- 不提交密钥、Token、私钥、证书、真实生产配置。
- 不为了提交而跳过测试或隐藏失败。
- 不在父目录误提交子仓内容。


## Git 状态处理

接入或提交前先判断 Git 状态：

| 状态 | 处理 |
|---|---|
| 当前目录已有 `.git` | 使用现有 Git，先看 `git status --short` |
| 没有 `.git` | 不自动 `git init`，先问用户 |
| 父目录有 `.git` | 先判断 monorepo，不在父目录误提交子仓内容 |
| 子仓各自有 `.git` | 每个子仓分别检查、分别提交 |
| 不确定 | 停下来报告目录结构和 Git 发现结果 |

新空项目在用户确认计划并明确说“执行”后，可以初始化 Git；老项目、旧代码目录、状态不明目录不适用。初始化后仍不自动创建 remote、不提交、不 push。

已有改动时先报告，不覆盖、不清理、不 stash。如果已有 AI 规则，生成 `.proposed`，不直接覆盖。

## 多仓工作区

如果项目被规划为多子仓，父级目录只做协调，Git 仓库建在各子目录里。

```text
workspace/
├── CLAUDE.md   # 工作区路由入口，可选
├── AGENTS.md   # 工作区路由入口，可选
├── backend/    # 独立 Git 仓库: backend/.git
└── frontend/   # 独立 Git 仓库: frontend/.git
```

- 父目录只做协调，不执行 `git init` / `git add` / `git commit` / `git push`。
- 父目录入口只做子仓路由和跨仓计划入口；完整 `.ai-spec` 位于各子仓。
- 每个子仓各自有 `CLAUDE.md` / `AGENTS.md`，指向本子仓 `.ai-spec`。
- 跨仓任务分别检查、分别提交；不要把多个仓库当成一个仓库提交。

如果发现父目录已有 `.git`，必须停下来报告，让用户确认是保留 monorepo、迁移为多子仓，还是暂不处理。不得自动移动、删除或重建 Git 历史。

## 分支命名

默认主分支是 `main`；老项目已有 `master`、`dev`、`develop` 或其它命名时尊重现状，不自动改名。

推荐工作分支：

```text
feature/<short-name>
fix/<short-name>
chore/<short-name>
docs/<short-name>
```

全栈任务前后端建议使用同名分支，便于关联。

## 提交信息

使用简洁 Conventional Commits：

```text
feat(scope): add workflow task api
fix(scope): repair empty state rendering
docs(scope): update contract notes
refactor(scope): split media gateway service
test(scope): add api smoke coverage
chore(scope): update local scripts
```

## 本地备份规范

在无 Git、Git 状态不干净、或需要替换已有规则文件时，优先使用本地备份或 `.proposed` 文件保护现场。

- 默认生成 `.proposed`，不覆盖原文件。
- 用户确认替换前，备份将被替换的规则文件，命名为 `<filename>.bak-YYYYMMDD-HHMMSS`。
- 不备份整个项目，不备份密钥、依赖目录、构建产物、临时缓存。
- 备份文件不提交，除非用户明确要求。

## 提交前检查

提交前至少确认：

1. 当前所在仓库正确。
2. `git status` 清楚。
3. `git diff` 只包含本次任务内容。
4. 已运行最小相关验证，或已说明无法验证原因。
5. 没有密钥和生产配置。
6. 没有用户未授权的删除、覆盖、格式化大改。
7. commit message 能说明本次改动。

推荐在 `git add` / `git commit` 前运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .ai-spec\scripts\git-preflight.ps1
```

```bash
bash .ai-spec/scripts/git-preflight.sh
```

脚本只扫描当前 Git 变更，重点拦截真实 `.env`、私钥/证书、常见 token、超大文件和构建产物路径。脚本通过不代表可以跳过 `git diff` 人工确认。

## 停止条件

遇到以下情况必须停下来问用户：

- 用户没有明确要求提交。
- 有不属于本次任务的改动。
- 发现密钥、生产配置或敏感数据。
- 需要 `git push`。
- 需要创建 MR/PR。
- 需要重写历史、rebase、reset、force push。
- 当前目录可能是父目录而不是具体子仓。


