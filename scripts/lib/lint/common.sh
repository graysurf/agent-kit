#!/usr/bin/env bash

lint_usage() {
  cat <<'USAGE'
Usage:
  scripts/lint.sh [all|shell|python]
  scripts/lint.sh [--all|--shell|--python]

Runs repo-local lint and syntax checks.

Subcommands:
  all (default): run both shell + python checks
  shell:         run shell checks only (bash + zsh)
  python:        run python checks only (ruff + mypy + pyright)

Setup:
  uv sync --locked

Examples:
  scripts/lint.sh
  scripts/lint.sh all
  scripts/lint.sh shell
  scripts/lint.sh --python
USAGE
}

lint_contains_path() {
  local needle="${1:-}"
  shift || true
  local path=''
  for path in "$@"; do
    if [[ "$path" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

lint_prepare_runtime_env() {
  local repo_root="${LINT_REPO_ROOT:-}"
  if [[ -z "$repo_root" ]]; then
    echo "error: LINT_REPO_ROOT is not set" >&2
    return 2
  fi

  cd "$repo_root"
  local agent_home="${AGENT_HOME:-$repo_root}"
  export AGENT_HOME="$agent_home"

  # Reduce color/control sequences for non-interactive usage and logs.
  export NO_COLOR=1
  export CLICOLOR=0
  export CLICOLOR_FORCE=0
  export FORCE_COLOR=0
  export PY_COLORS=0
}
