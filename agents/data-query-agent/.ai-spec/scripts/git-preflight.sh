#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-}"
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
fi

errors=()
warnings=()

if ! git -C "$PROJECT_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  errors+=("Not a Git repository: $PROJECT_ROOT")
else
  GIT_ROOT="$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel)"
  if [ "$(cd "$PROJECT_ROOT" && pwd)" != "$(cd "$GIT_ROOT" && pwd)" ]; then
    warnings+=("Project root differs from Git root: project=$PROJECT_ROOT git=$GIT_ROOT")
  fi
  if [ -n "$(git -C "$GIT_ROOT" status --short)" ]; then
    warnings+=("Working tree has changes; review git status before commit.")
  fi

  changed=()
  while IFS= read -r item; do
    changed+=("$item")
  done < <(
    {
      git -C "$GIT_ROOT" diff --name-only --cached
      git -C "$GIT_ROOT" diff --name-only
      git -C "$GIT_ROOT" ls-files --others --exclude-standard
    } | awk '!seen[$0]++'
  )

  for rel in "${changed[@]}"; do
    [ -n "$rel" ] || continue
    normalized="${rel//\\//}"
    if [[ "$normalized" =~ (^|/)(node_modules|vendor|dist|build|coverage|\.next|out|target|bin|obj)(/|$) ]]; then
      warnings+=("Generated/dependency path changed: $rel")
    fi

    abs="$GIT_ROOT/$rel"
    [ -f "$abs" ] || continue

    size="$(wc -c < "$abs" | tr -d ' ')"
    if [ "$size" -gt 26214400 ]; then
      errors+=("Very large changed file: $rel")
    elif [ "$size" -gt 5242880 ]; then
      warnings+=("Large changed file: $rel")
    fi

    if [[ "$normalized" =~ (^|/)\.env(\.|$) ]] && [[ ! "$normalized" =~ \.env(\..*)?\.(example|sample|template|dist)$|\.env\.(example|sample|template|dist)$ ]]; then
      errors+=("Real environment file changed: $rel")
    fi

    if [[ "$normalized" =~ (^|/)(id_rsa|id_ed25519|id_dsa|id_ecdsa)$|\.(pem|p12|pfx|key)$ ]]; then
      errors+=("Sensitive key/certificate path changed: $rel")
    fi

    case "$normalized" in
      *.png|*.jpg|*.jpeg|*.gif|*.webp|*.ico|*.pdf|*.zip|*.7z|*.rar|*.gz|*.tar|*.exe|*.dll|*.woff|*.woff2|*.ttf|*.otf|*.mp3|*.mp4|*.mov)
        continue
        ;;
    esac
    [ "$size" -le 2097152 ] || continue

    if grep -Eq -- '-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{36,}|sk-[A-Za-z0-9]{20,}' "$abs" 2>/dev/null; then
      errors+=("Possible secret in changed file: $rel")
      continue
    fi
    if grep -Eiv 'changeme|example|placeholder|todo|xxx|<|your_|YOUR_|dummy|test' "$abs" 2>/dev/null |
      grep -Eiq "^[[:space:]]*[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|PRIVATE_KEY|API_KEY|ACCESS_KEY)[A-Z0-9_]*[[:space:]]*=[[:space:]]*[\"']?[^#[:space:]]{8,}"; then
      errors+=("Possible secret in changed file: $rel")
    fi
  done
fi

if [ "${#errors[@]}" -gt 0 ]; then
  echo "Git preflight failed: $PROJECT_ROOT"
  for item in "${errors[@]}"; do echo "ERROR $item"; done
  for item in "${warnings[@]}"; do echo "WARN $item"; done
  exit 1
fi

echo "Git preflight passed: $PROJECT_ROOT"
for item in "${warnings[@]}"; do echo "WARN $item"; done
