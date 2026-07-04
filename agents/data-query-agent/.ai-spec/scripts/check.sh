#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -n "$PROJECT_ROOT" ]; then
  PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
  SPEC_ROOT="$PROJECT_ROOT/.ai-spec"
elif [ -d "$(pwd)/.ai-spec" ]; then
  PROJECT_ROOT="$(pwd)"
  SPEC_ROOT="$PROJECT_ROOT/.ai-spec"
elif [ "$(basename "$SPEC_ROOT")" = ".ai-spec" ]; then
  PROJECT_ROOT="$(cd "$SPEC_ROOT/.." && pwd)"
else
  PROJECT_ROOT="$SPEC_ROOT"
fi

errors=()
warnings=()

require_file() {
  [ -f "$SPEC_ROOT/$1" ] || errors+=("Missing file: $1")
}

require_dir() {
  [ -d "$SPEC_ROOT/$1" ] || errors+=("Missing directory: $1")
}

required_files=(
  "README.md"
  "CLAUDE.md"
  "AGENTS.md"
  ".ai-rules/README.md"
  ".ai-rules/redlines.md"
  ".ai-rules/task-routing.md"
  ".ai-rules/context-loading.md"
  ".ai-rules/documentation-policy.md"
  ".ai-rules/git-workflow.md"
  ".ai-rules/modularity-output.md"
  ".ai-rules/skill-contract.md"
  ".ai-rules/project-facts.example.md"
  "docs/rules/business-rules.example.md"
  "docs/plans/README.md"
  "docs/plans/project-plan.example.md"
  "docs/plans/current.example.md"
  "docs/plans/bugfix-review-plan.example.md"
  "skills/README.md"
  "scripts/create-entry.ps1"
  "scripts/create-entry.cmd"
  "scripts/create-entry.sh"
  "scripts/refresh-project-facts.ps1"
  "scripts/refresh-project-facts.sh"
  "scripts/git-preflight.ps1"
  "scripts/git-preflight.sh"
  "scripts/check.ps1"
  "scripts/check.sh"
)

for dir in skills .ai-rules docs docs/rules scripts; do
  require_dir "$dir"
done
for file in "${required_files[@]}"; do
  require_file "$file"
done

if [ -d "$SPEC_ROOT/skills" ]; then
  found_skill=0
  for skill_dir in "$SPEC_ROOT"/skills/*; do
    [ -d "$skill_dir" ] || continue
    found_skill=1
    skill_file="$skill_dir/SKILL.md"
    name="skills/$(basename "$skill_dir")/SKILL.md"
    if [ ! -f "$skill_file" ]; then
      errors+=("Missing SKILL.md: $name")
      continue
    fi
    grep -q '^---' "$skill_file" || errors+=("Invalid frontmatter: $name")
    grep -q '^name:' "$skill_file" || errors+=("Missing name in frontmatter: $name")
    grep -q '^description:' "$skill_file" || errors+=("Missing description in frontmatter: $name")
    for section in "## 目标" "## 适用场景" "## 不适用场景" "## 最小上下文" "## 工作流" "## 停止条件" "## 强制执行规则"; do
      grep -qF "$section" "$skill_file" || errors+=("Missing section $section: $name")
    done
    grep -q "验证" "$skill_file" || errors+=("Missing verification guidance: $name")
  done
  [ "$found_skill" = "1" ] || errors+=("No skill directories found under skills/.")
fi

if [ "$(basename "$SPEC_ROOT")" = ".ai-spec" ]; then
  [ -f "$PROJECT_ROOT/CLAUDE.md" ] || warnings+=("Project root entry missing: CLAUDE.md. Run bash .ai-spec/scripts/create-entry.sh")
  [ -f "$PROJECT_ROOT/AGENTS.md" ] || warnings+=("Project root entry missing: AGENTS.md. Run bash .ai-spec/scripts/create-entry.sh")
fi

line_budget() {
  local label="$1"
  local path="$2"
  local max="$3"
  [ -e "$path" ] || return
  local count
  count="$(wc -l < "$path" | tr -d ' ')"
  if [ "$count" -gt "$max" ]; then
    warnings+=("Size budget exceeded: $label has $count lines, budget $max. Consider splitting or slimming.")
  fi
}

line_budget "README.md" "$SPEC_ROOT/README.md" 180
for file in "$SPEC_ROOT"/.ai-rules/*.md; do
  [ -f "$file" ] || continue
  [ "$(basename "$file")" = "project-facts.md" ] && continue
  line_budget ".ai-rules/$(basename "$file")" "$file" 160
done
for file in "$SPEC_ROOT"/skills/*/SKILL.md; do
  [ -f "$file" ] || continue
  line_budget "skills/$(basename "$(dirname "$file")")/SKILL.md" "$file" 120
done

if [ "${#errors[@]}" -gt 0 ]; then
  echo "Template check failed: $SPEC_ROOT"
  for item in "${errors[@]}"; do echo "ERROR $item"; done
  for item in "${warnings[@]}"; do echo "WARN $item"; done
  exit 1
fi

echo "Template check passed: $SPEC_ROOT"
for item in "${warnings[@]}"; do echo "WARN $item"; done
