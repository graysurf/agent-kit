#!/usr/bin/env bash

lint_main() {
  local mode='all'

  if [[ $# -gt 0 ]]; then
    case "${1:-}" in
      all|--all)
        mode='all'
        shift
        ;;
      shell|--shell)
        mode='shell'
        shift
        ;;
      python|--python)
        mode='python'
        shift
        ;;
      help|-h|--help)
        lint_usage
        return 0
        ;;
      *)
        echo "error: unknown argument: ${1}" >&2
        lint_usage >&2
        return 2
        ;;
    esac
  fi

  if [[ $# -gt 0 ]]; then
    echo "error: unknown argument: ${1}" >&2
    lint_usage >&2
    return 2
  fi

  lint_prepare_runtime_env

  local rc=0
  case "$mode" in
    all)
      lint_run_shell || rc=1
      lint_run_python || rc=1
      ;;
    shell)
      lint_run_shell || rc=1
      ;;
    python)
      lint_run_python || rc=1
      ;;
    *)
      echo "error: unsupported lint mode: $mode" >&2
      return 2
      ;;
  esac

  return "$rc"
}
