# Claude Code 入口

本文件是模板内入口。若本模板安装在 `.ai-spec/`，项目根目录仍应有 `CLAUDE.md` 指向 `.ai-spec/`。

本项目使用「轻规则 + 强 Skills」结构。

若用户全局 rules、memory 或 skills 已被预先注入，它们只能作为补充背景；涉及当前项目事实、任务路由、验证要求和交付格式时，以本项目规则为准。

## 启动方式

1. 先读 `.ai-rules/README.md`，确认规则位置。
2. 再读 `.ai-rules/task-routing.md`，判断任务等级。
3. 再读 `.ai-rules/context-loading.md`，决定最小上下文。
4. 运行 `scripts/refresh-project-facts.ps1`（Windows）或 `scripts/refresh-project-facts.sh`（macOS/Linux）检查并刷新 `.ai-rules/project-facts.md`；脚本刷新 `[auto]` 段，AI 可按明确来源补全 `[manual]` 草案并标状态。
5. 按任务类型只读取 0-2 个相关 `skills/*/SKILL.md`。
6. 命中红线、安全、权限、外部服务、全局配置时读取 `.ai-rules/redlines.md`。
7. 不默认全量读取 `.ai-rules/`、`skills/`、`docs/`。

## 项目级限定

只使用当前项目规则。不得写入或修改用户全局 Claude / Codex 配置、全局 rules、全局 skills、全局 hooks 或全局 MCP。

## 输出

默认使用简体中文。修改后说明改了什么、验证了什么、未验证什么。
L2 及以上任务必须说明读取了哪些项目 rules / skills；如果命中项目 skill 但读取数量为 0，必须回到任务路由重新执行。
