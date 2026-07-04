#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
PROJECT_ROOT=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    *) PROJECT_ROOT="$arg" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$PROJECT_ROOT" ]; then
  if [ "$(basename "$SPEC_ROOT")" = ".ai-spec" ]; then
    PROJECT_ROOT="$(cd "$SPEC_ROOT/.." && pwd)"
  elif [ -d "$(pwd)/.ai-spec" ]; then
    PROJECT_ROOT="$(pwd)"
  else
    PROJECT_ROOT="$(pwd)"
  fi
else
  PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
fi

if [ ! -d "$PROJECT_ROOT/.ai-spec" ]; then
  echo "Cannot find .ai-spec under project root: $PROJECT_ROOT" >&2
  exit 1
fi

available_target() {
  local path="$1"
  if [ ! -e "$path" ]; then
    printf '%s' "$path"
    return
  fi
  if [ ! -e "$path.proposed" ]; then
    printf '%s' "$path.proposed"
    return
  fi
  printf '%s' "$path.proposed-$(date +%Y%m%d-%H%M%S)"
}

write_file() {
  local path="$1"
  local content="$2"
  local target
  target="$(available_target "$path")"
  if [ "$DRY_RUN" = "1" ]; then
    echo "DRYRUN $target"
    return
  fi
  printf '%s\n' "$content" > "$target"
  echo "WROTE $target"
}

CLAUDE_CONTENT='# Claude Code 入口

本项目规则位于 `.ai-spec/`。

若用户全局 rules、memory 或 skills 已被预先注入，它们只能作为补充背景；涉及当前项目事实、任务路由、验证要求和交付格式时，以本项目规则为准。

请先读取 `.ai-spec/.ai-rules/README.md`，再按任务等级读取：
- `.ai-spec/.ai-rules/task-routing.md`
- `.ai-spec/.ai-rules/context-loading.md`
- 命中的 `.ai-spec/skills/*/SKILL.md`

启动或接管任务时，运行 `.ai-spec/scripts/refresh-project-facts.ps1`（Windows）或 `.ai-spec/scripts/refresh-project-facts.sh`（macOS/Linux）检查并刷新 `.ai-spec/.ai-rules/project-facts.md`；脚本刷新 `[auto]` 段。AI 可按明确来源补全 `[manual]` 草案，必须写来源和状态，未知项标待确认。

命中红线、安全、权限、外部服务、全局配置时读取：
- `.ai-spec/.ai-rules/redlines.md`

只使用当前项目规则。不得写入或修改用户全局 Claude / Codex 配置、全局 rules、全局 skills、全局 hooks 或全局 MCP。

不要默认全量读取 `.ai-spec/`。

L2 及以上任务必须说明读取了哪些项目 rules / skills；如果命中项目 skill 但读取数量为 0，必须回到任务路由重新执行。'

AGENTS_CONTENT='# Codex 入口

本项目规则位于 `.ai-spec/`。

若用户全局 rules、memory 或 skills 已被预先注入，它们只能作为补充背景；涉及当前项目事实、任务路由、验证要求和交付格式时，以本项目规则为准。

Codex 必须先遵守系统/开发者指令，再读取：
- `.ai-spec/.ai-rules/README.md`
- `.ai-spec/.ai-rules/task-routing.md`
- `.ai-spec/.ai-rules/context-loading.md`
- 命中的 `.ai-spec/skills/*/SKILL.md`

启动或接管任务时，运行 `.ai-spec/scripts/refresh-project-facts.ps1`（Windows）或 `.ai-spec/scripts/refresh-project-facts.sh`（macOS/Linux）检查并刷新 `.ai-spec/.ai-rules/project-facts.md`；脚本刷新 `[auto]` 段。AI 可按明确来源补全 `[manual]` 草案，必须写来源和状态，未知项标待确认。

命中红线、安全、权限、外部服务、全局配置时读取：
- `.ai-spec/.ai-rules/redlines.md`

只使用当前项目规则。不得写入或修改用户全局 Claude / Codex 配置、全局 rules、全局 skills、全局 hooks 或全局 MCP。

不要默认全量读取 `.ai-spec/`。

L2 及以上任务必须说明读取了哪些项目 rules / skills；如果命中项目 skill 但读取数量为 0，必须回到任务路由重新执行。'

write_file "$PROJECT_ROOT/CLAUDE.md" "$CLAUDE_CONTENT"
write_file "$PROJECT_ROOT/AGENTS.md" "$AGENTS_CONTENT"
