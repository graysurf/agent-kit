#!/usr/bin/env bash
#
# Stop hook: emit a one-shot PR readiness reminder for non-trivial branch diffs.
#
set -uo pipefail

command -v git >/dev/null 2>&1 || exit 0
command -v cksum >/dev/null 2>&1 || exit 0
python_bin="$(command -v python3 || true)"
[[ -z "$python_bin" ]] && exit 0

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "$repo_root" ]] && exit 0
cd "$repo_root" 2>/dev/null || exit 0

base_branch=""
for candidate in main master; do
  if git rev-parse --verify --quiet "$candidate" >/dev/null 2>&1; then
    base_branch="$candidate"
    break
  fi
done
[[ -z "$base_branch" ]] && exit 0

current_branch="$(git symbolic-ref --short -q HEAD 2>/dev/null || true)"
[[ "$current_branch" == "$base_branch" ]] && exit 0

head_sha="$(git rev-parse HEAD 2>/dev/null || true)"
[[ -z "$head_sha" ]] && exit 0

diff_files="$(git diff --name-only "$base_branch"...HEAD 2>/dev/null || true)"
[[ -z "$diff_files" ]] && exit 0

has_nontrivial=0
while IFS= read -r file_path; do
  [[ -z "$file_path" ]] && continue
  case "$file_path" in
    *.md) ;;
    *) has_nontrivial=1; break ;;
  esac
done <<< "$diff_files"
[[ "$has_nontrivial" -eq 0 ]] && exit 0

repo_hash="$(printf '%s' "$repo_root" | cksum | awk '{print $1}')"
stamp_dir="$HOME/.cache/agent-kit"
stamp="$stamp_dir/pr-readiness-${repo_hash}-${head_sha}.stamp"
[[ -f "$stamp" ]] && exit 0

repo_name="$(basename "$repo_root")"
msg="non-trivial changes in ${repo_name} since ${base_branch} - consider running project validation / PR readiness checks before pushing"

MSG="$msg" "$python_bin" -c '
import json
import os

print(json.dumps({"systemMessage": os.environ["MSG"]}))
'

mkdir -p "$stamp_dir"
: > "$stamp"
