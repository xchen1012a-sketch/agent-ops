#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=""
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    *) PROJECT_ROOT="$arg" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$PROJECT_ROOT" ]; then
  if [ -d "$(pwd)/.ai-spec" ]; then
    PROJECT_ROOT="$(pwd)"
  elif [ "$(basename "$SPEC_ROOT")" = ".ai-spec" ]; then
    PROJECT_ROOT="$(cd "$SPEC_ROOT/.." && pwd)"
  else
    PROJECT_ROOT="$SPEC_ROOT"
  fi
else
  PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
  SPEC_ROOT="$PROJECT_ROOT/.ai-spec"
fi

RULES_ROOT="$SPEC_ROOT/.ai-rules"
FACTS_PATH="$RULES_ROOT/project-facts.md"
if [ ! -d "$RULES_ROOT" ]; then
  echo "Cannot find .ai-rules under spec root: $SPEC_ROOT" >&2
  exit 1
fi

hash_text() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  else
    shasum -a 256 | awk '{print $1}'
  fi
}

file_hash() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

json_extract() {
  local expr="$1"
  local file="$2"
  if [ ! -f "$file" ] || ! command -v node >/dev/null 2>&1; then
    return 0
  fi
  node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
$expr
" "$file"
}

tech_stack() {
  local pkg="$PROJECT_ROOT/package.json"
  json_extract "
const deps = Object.assign({}, pkg.dependencies || {}, pkg.devDependencies || {});
const known = ['next','react','vue','svelte','vite','typescript','express','fastify','nestjs','@nestjs/core','drizzle-orm','prisma','@prisma/client','typeorm','sequelize','mysql2','pg','sqlite3','better-sqlite3','redis','ioredis','vitest','jest','playwright','@playwright/test','cypress','eslint','prettier','tailwindcss'];
const found = known.filter((name) => deps[name]).map((name) => '- ' + name + ' ' + deps[name]);
console.log(found.length ? found.join('\n') : '- No common framework or tool detected from package.json.');
" "$pkg"
  if [ ! -f "$pkg" ] || ! command -v node >/dev/null 2>&1; then
    echo "- No package.json parser available."
  fi
}

script_lines() {
  local pkg="$PROJECT_ROOT/package.json"
  json_extract "
const scripts = pkg.scripts || {};
const names = Object.keys(scripts).sort();
console.log(names.length ? names.map((name) => '- ' + name + ': ' + scripts[name]).join('\n') : '- No package.json scripts detected.');
" "$pkg"
  if [ ! -f "$pkg" ] || ! command -v node >/dev/null 2>&1; then
    echo "- No package.json scripts detected."
  fi
}

env_keys() {
  local found=0
  while IFS= read -r -d '' file; do
    while IFS= read -r key; do
      [ -n "$key" ] || continue
      printf '%s\n' "$key"
      found=1
    done < <(sed -nE 's/^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=.*/- \1/p' "$file")
  done < <(find "$PROJECT_ROOT" -maxdepth 1 -type f \( -name ".env*.example" -o -name ".env.example" \) -print0 2>/dev/null)
  if [ "$found" = "0" ]; then
    echo "- No .env*.example keys detected."
  fi
}

directory_tree() {
  local root_name
  root_name="$(basename "$PROJECT_ROOT")"
  echo "$root_name/"
  find "$PROJECT_ROOT" -mindepth 1 -maxdepth 2 \
    \( -name .git -o -name .ai-spec -o -name .agents -o -name .codex -o -name node_modules -o -name .next -o -name dist -o -name build -o -name coverage -o -name .turbo -o -name .cache -o -name project-facts.md \) -prune \
    -o -print 2>/dev/null |
    sed "s#^$PROJECT_ROOT/##" |
    sort |
    head -n 80 |
    awk '{
      depth=gsub("/", "/");
      if (depth == 0) prefix="|-- "; else prefix="|   |-- ";
      print prefix $0
    }'
}

git_facts() {
  if ! git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "- No valid Git repository detected."
    return
  fi
  local branch
  branch="$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || true)"
  [ -n "$branch" ] || branch="(detached or unknown)"
  echo "- Current branch: $branch"
  if [ -n "$(git -C "$PROJECT_ROOT" status --short 2>/dev/null)" ]; then
    echo "- Working tree: has uncommitted changes"
  else
    echo "- Working tree: clean"
  fi
  local remotes
  remotes="$(git -C "$PROJECT_ROOT" remote -v 2>/dev/null | head -n 4 || true)"
  if [ -n "$remotes" ]; then
    echo "- Remotes:"
    printf '%s\n' "$remotes" | sed 's/^/  - /'
  else
    echo "- Remotes: none"
  fi
}

manual_section() {
  if [ -f "$FACTS_PATH" ] && grep -q '<!-- ai-facts:manual:start -->' "$FACTS_PATH"; then
    awk '/<!-- ai-facts:manual:start -->/{on=1} on{print} /<!-- ai-facts:manual:end -->/{on=0}' "$FACTS_PATH"
    return
  fi
  local example="$RULES_ROOT/project-facts.example.md"
  if [ -f "$example" ]; then
    awk '/<!-- ai-facts:manual:start -->/{on=1} on{print} /<!-- ai-facts:manual:end -->/{on=0}' "$example"
  fi
}

TREE_LINES="$(directory_tree)"
SOURCE_PARTS=""
for name in package.json package-lock.json pnpm-lock.yaml yarn.lock bun.lockb tsconfig.json .env.example .env.local.example; do
  if [ -f "$PROJECT_ROOT/$name" ]; then
    SOURCE_PARTS="${SOURCE_PARTS}FILE:$name
$(file_hash "$PROJECT_ROOT/$name")
"
  fi
done
SOURCE_HASH="$(printf '%s\nTREE:\n%s\n' "$SOURCE_PARTS" "$TREE_LINES" | hash_text | cut -c1-16)"

if [ "$FORCE" = "0" ] && [ -f "$FACTS_PATH" ] && grep -q "source hash: $SOURCE_HASH" "$FACTS_PATH"; then
  echo "Project facts already fresh: $FACTS_PATH"
  exit 0
fi

REFRESH_TIME="$(date '+%Y-%m-%d %H:%M:%S %z')"
TECH_LINES="$(tech_stack)"
SCRIPT_LINES="$(script_lines)"
ENV_LINES="$(env_keys | sort -u)"
GIT_LINES="$(git_facts)"
MANUAL_SECTION="$(manual_section)"

cat > "$FACTS_PATH" <<EOF
# Project facts

> [auto] is refreshed by AI or scripts from repository state and only records verifiable facts.
> [manual] may be filled by AI from explicit sources and confirmed by humans. AI must mark uncertain entries as pending confirmation.

<!-- ai-facts:auto:start -->
## [auto] Refresh info

- source hash: $SOURCE_HASH
- last refresh: $REFRESH_TIME
- refresh command: scripts/refresh-project-facts.sh

## [auto] Tech stack

$TECH_LINES

## [auto] Scripts

$SCRIPT_LINES

## [auto] Directory structure (top 2 levels)

\`\`\`text
$TREE_LINES
\`\`\`

## [auto] Environment keys

$ENV_LINES

## [auto] Git status

$GIT_LINES
<!-- ai-facts:auto:end -->

$MANUAL_SECTION
EOF

echo "Project facts refreshed: $FACTS_PATH"
