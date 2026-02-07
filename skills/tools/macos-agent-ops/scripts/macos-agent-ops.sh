#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  macos-agent-ops.sh where
  macos-agent-ops.sh doctor
  macos-agent-ops.sh app-check --app <name> [--wait-ms <ms>] [--timeout-ms <ms>] [--poll-ms <ms>]
  macos-agent-ops.sh scenario --file <scenario.json>
  macos-agent-ops.sh run -- <macos-agent args...>

Notes:
  - Requires Homebrew-installed macos-agent available on PATH.
USAGE
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "error: macos-agent-ops requires macOS" >&2
    exit 1
  fi
}

resolve_bin() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "error: Homebrew is required to run macos-agent-ops" >&2
    echo "hint: install Homebrew, then run: brew install macos-agent" >&2
    exit 1
  fi

  local brew_prefix=''
  local brew_bin=''
  brew_bin="$(command -v macos-agent || true)"
  if [[ -z "$brew_bin" ]]; then
    echo "error: macos-agent not found on PATH" >&2
    echo "hint: install with Homebrew: brew install macos-agent" >&2
    exit 1
  fi

  brew_prefix="$(brew --prefix 2>/dev/null || true)"
  if [[ -z "$brew_prefix" ]]; then
    echo "error: unable to determine Homebrew prefix" >&2
    exit 1
  fi

  if [[ "$brew_bin" != "$brew_prefix/bin/macos-agent" ]]; then
    echo "error: macos-agent must use Homebrew binary: $brew_prefix/bin/macos-agent" >&2
    echo "found: $brew_bin" >&2
    exit 1
  fi

  printf '%s\n' "$brew_bin"
}

run_doctor() {
  local bin
  bin="$(resolve_bin)"
  command -v cliclick >/dev/null 2>&1 || {
    echo "error: cliclick not found on PATH" >&2
    exit 1
  }
  "$bin" --format json preflight --include-probes
}

run_app_check() {
  local app=''
  local wait_ms="1800"
  local timeout_ms="12000"
  local poll_ms="60"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --app)
        app="${2:-}"
        shift 2
        ;;
      --wait-ms)
        wait_ms="${2:-}"
        shift 2
        ;;
      --timeout-ms)
        timeout_ms="${2:-}"
        shift 2
        ;;
      --poll-ms)
        poll_ms="${2:-}"
        shift 2
        ;;
      *)
        echo "error: unknown argument for app-check: $1" >&2
        exit 2
        ;;
    esac
  done

  if [[ -z "$app" ]]; then
    echo "error: --app is required" >&2
    exit 2
  fi

  local bin
  bin="$(resolve_bin)"

  osascript -e "tell application \"$app\" to launch" >/dev/null
  "$bin" --format json --timeout-ms "$timeout_ms" window activate --app "$app" --wait-ms "$wait_ms"
  "$bin" --format json wait app-active --app "$app" --timeout-ms "$timeout_ms" --poll-ms "$poll_ms"
}

run_scenario() {
  local scenario_file=''
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --file)
        scenario_file="${2:-}"
        shift 2
        ;;
      *)
        echo "error: unknown argument for scenario: $1" >&2
        exit 2
        ;;
    esac
  done

  if [[ -z "$scenario_file" ]]; then
    echo "error: --file is required" >&2
    exit 2
  fi
  if [[ ! -f "$scenario_file" ]]; then
    echo "error: scenario file not found: $scenario_file" >&2
    exit 1
  fi

  local bin
  bin="$(resolve_bin)"
  "$bin" --format json scenario run --file "$scenario_file"
}

run_passthrough() {
  if [[ "$1" != "--" ]]; then
    echo "error: run requires '--' before macos-agent args" >&2
    exit 2
  fi
  shift
  if [[ $# -eq 0 ]]; then
    echo "error: run requires at least one macos-agent argument" >&2
    exit 2
  fi

  local bin
  bin="$(resolve_bin)"
  "$bin" "$@"
}

main() {
  require_macos

  local cmd="${1:-}"
  if [[ -z "$cmd" ]]; then
    usage >&2
    exit 2
  fi
  shift || true

  case "$cmd" in
    where)
      resolve_bin
      ;;
    doctor)
      run_doctor
      ;;
    app-check)
      run_app_check "$@"
      ;;
    scenario)
      run_scenario "$@"
      ;;
    run)
      run_passthrough "$@"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "error: unknown command: $cmd" >&2
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
