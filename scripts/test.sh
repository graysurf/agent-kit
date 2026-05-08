#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/test.sh [pytest args...]

Runs the local pytest suite using the uv-managed project environment.

Setup:
  uv sync --locked

Examples:
  scripts/test.sh
  scripts/test.sh -m script_regression -k plan-issue-adapter

Defaults:
  - Ignores repo-local worktree mirrors (`worktrees/`, `.worktrees/`) to avoid
    pytest import-path collisions.
  - Set `CODEX_PYTEST_INCLUDE_WORKTREES=1` to disable this ignore behavior.
USAGE
}

if [[ "${1-}" == "-h" || "${1-}" == "--help" ]]; then
  usage
  exit 0
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

uv_bin="$(command -v uv || true)"
if [[ -z "$uv_bin" ]]; then
  echo "error: uv not found; install uv and run: uv sync --locked" >&2
  exit 1
fi

agent_home="${AGENT_HOME:-$repo_root}"
export AGENT_HOME="$agent_home"
declare -a ignore_args=()
if [[ "${CODEX_PYTEST_INCLUDE_WORKTREES:-}" != "1" ]]; then
  ignore_args+=(--ignore=worktrees --ignore=.worktrees)
fi

set +e
"$uv_bin" run --locked pytest "${ignore_args[@]}" "$@"
status=$?
set -e

coverage_md="${AGENT_HOME}/out/tests/script-coverage/summary.md"
coverage_json="${AGENT_HOME}/out/tests/script-coverage/summary.json"
if [[ -f "$coverage_md" ]]; then
  echo ""
  echo "script coverage (functional):"
  echo "  - $coverage_md"
  if [[ -f "$coverage_json" ]]; then
    echo "  - $coverage_json"
  fi
fi

exit "$status"
