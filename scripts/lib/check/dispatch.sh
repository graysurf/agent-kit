#!/usr/bin/env bash

check_repo_root_for_dispatch() {
  if [[ -n "${CHECK_REPO_ROOT:-}" ]]; then
    printf '%s\n' "$CHECK_REPO_ROOT"
    return 0
  fi

  local dispatch_dir=''
  dispatch_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  printf '%s\n' "$(cd "${dispatch_dir}/../../.." && pwd -P)"
}

CHECK_REPO_ROOT="$(check_repo_root_for_dispatch)"
source "${CHECK_REPO_ROOT}/scripts/lib/check/modes.sh"

check_usage() {
  cat <<'USAGE'
Usage:
  scripts/check.sh [--lint] [--lint-shell] [--lint-python] [--markdown] [--third-party] [--contracts] [--skills-layout] [--env-bools] [--docs] [--entrypoint-ownership] [--tests] [--semgrep] [--all] [--pre-commit] [--] [pytest args...]
  scripts/check.sh [lint] [lint-shell] [lint-python] [markdown] [third-party] [contracts] [skills-layout] [env-bools] [docs] [entrypoint-ownership] [tests] [semgrep] [all] [pre-commit] [--] [pytest args...]

Runs repo-local checks (shell/python lint, markdown lint, skill contracts, env-bools, optional Semgrep, pytest).

Setup:
  .venv/bin/pip install -r requirements-dev.txt

Examples:
  scripts/check.sh all
  scripts/check.sh --all
  scripts/check.sh pre-commit
  scripts/check.sh --pre-commit
  scripts/check.sh docs
  scripts/check.sh --tests -- -m script_smoke
USAGE
}

check_reset_state() {
  CHECK_RUN_LINT=0
  CHECK_RUN_LINT_SHELL=0
  CHECK_RUN_LINT_PYTHON=0
  CHECK_RUN_MARKDOWN=0
  CHECK_RUN_THIRD_PARTY=0
  CHECK_RUN_CONTRACTS=0
  CHECK_RUN_SKILL_LAYOUT=0
  CHECK_RUN_ENV_BOOLS=0
  CHECK_RUN_DOCS=0
  CHECK_RUN_ENTRYPOINT_OWNERSHIP=0
  CHECK_RUN_TESTS=0
  CHECK_RUN_SEMGREP=0
  CHECK_RUN_STALE_SKILL_AUDIT=0
  CHECK_SEEN_PYTEST_ARGS=0
  CHECK_PYTEST_ARGS=()
  CHECK_PARSE_RESULT='run'
  CHECK_SEMGREP_SUMMARY_LIMIT="${SEMGREP_SUMMARY_LIMIT:-5}"
}

check_enable_mode() {
  local mode="${1:-}"
  case "$mode" in
    lint)
      CHECK_RUN_LINT=1
      ;;
    lint-shell)
      CHECK_RUN_LINT_SHELL=1
      ;;
    lint-python)
      CHECK_RUN_LINT_PYTHON=1
      ;;
    markdown)
      CHECK_RUN_MARKDOWN=1
      ;;
    third-party)
      CHECK_RUN_THIRD_PARTY=1
      ;;
    contracts)
      CHECK_RUN_CONTRACTS=1
      ;;
    skills-layout)
      CHECK_RUN_SKILL_LAYOUT=1
      ;;
    env-bools)
      CHECK_RUN_ENV_BOOLS=1
      ;;
    docs)
      CHECK_RUN_DOCS=1
      ;;
    entrypoint-ownership)
      CHECK_RUN_ENTRYPOINT_OWNERSHIP=1
      ;;
    tests)
      CHECK_RUN_TESTS=1
      ;;
    semgrep)
      CHECK_RUN_SEMGREP=1
      ;;
    all)
      CHECK_RUN_LINT=1
      CHECK_RUN_MARKDOWN=1
      CHECK_RUN_THIRD_PARTY=1
      CHECK_RUN_CONTRACTS=1
      CHECK_RUN_SKILL_LAYOUT=1
      CHECK_RUN_ENV_BOOLS=1
      CHECK_RUN_DOCS=1
      CHECK_RUN_TESTS=1
      CHECK_RUN_SEMGREP=1
      ;;
    pre-commit)
      check_enable_mode all
      CHECK_RUN_STALE_SKILL_AUDIT=1
      CHECK_RUN_ENTRYPOINT_OWNERSHIP=1
      ;;
    *)
      return 1
      ;;
  esac
  return 0
}

check_parse_mode_token() {
  local token="${1:-}"
  if [[ "$token" == --* ]]; then
    token="${token#--}"
  fi
  printf '%s\n' "$token"
}

check_parse_args() {
  check_reset_state

  while [[ $# -gt 0 ]]; do
    case "${1:-}" in
      --)
        CHECK_SEEN_PYTEST_ARGS=1
        shift
        CHECK_PYTEST_ARGS=("$@")
        break
        ;;
      -h|--help|help)
        check_usage
        CHECK_PARSE_RESULT='help'
        return 0
        ;;
      *)
        local parsed_mode=''
        parsed_mode="$(check_parse_mode_token "${1:-}")"
        if ! check_mode_is_known "$parsed_mode"; then
          echo "error: unknown argument: ${1}" >&2
          check_usage >&2
          return 2
        fi
        check_enable_mode "$parsed_mode"
        shift
        ;;
    esac
  done

  if [[ "$CHECK_SEEN_PYTEST_ARGS" -eq 1 && "$CHECK_RUN_TESTS" -eq 0 ]]; then
    echo "error: pytest args provided without --tests/--all/--pre-commit" >&2
    check_usage >&2
    return 2
  fi

  if [[ "$CHECK_RUN_LINT" -eq 0 && "$CHECK_RUN_LINT_SHELL" -eq 0 && "$CHECK_RUN_LINT_PYTHON" -eq 0 && "$CHECK_RUN_MARKDOWN" -eq 0 && "$CHECK_RUN_THIRD_PARTY" -eq 0 && "$CHECK_RUN_CONTRACTS" -eq 0 && "$CHECK_RUN_SKILL_LAYOUT" -eq 0 && "$CHECK_RUN_ENV_BOOLS" -eq 0 && "$CHECK_RUN_DOCS" -eq 0 && "$CHECK_RUN_ENTRYPOINT_OWNERSHIP" -eq 0 && "$CHECK_RUN_TESTS" -eq 0 && "$CHECK_RUN_SEMGREP" -eq 0 && "$CHECK_RUN_STALE_SKILL_AUDIT" -eq 0 ]]; then
    check_usage
    CHECK_PARSE_RESULT='noop'
    return 0
  fi

  CHECK_PARSE_RESULT='run'
  return 0
}

check_prepare_runtime_env() {
  local repo_root="${CHECK_REPO_ROOT:-}"
  if [[ -z "$repo_root" ]]; then
    echo "error: CHECK_REPO_ROOT is not set" >&2
    return 2
  fi

  cd "$repo_root"
  local agent_home="${AGENT_HOME:-$repo_root}"
  export AGENT_HOME="$agent_home"
}

check_main() {
  check_parse_args "$@" || return $?

  if [[ "$CHECK_PARSE_RESULT" == 'help' || "$CHECK_PARSE_RESULT" == 'noop' ]]; then
    return 0
  fi

  check_prepare_runtime_env || return $?
  check_run_selected
}

