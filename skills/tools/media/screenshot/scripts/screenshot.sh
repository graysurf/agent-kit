#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  screenshot.sh [--help] [--] <screen-record args...>

Thin wrapper around the `screen-record` CLI.

Behavior:
  - If you pass a mode flag (`--list-windows`, `--list-apps`, `--preflight`,
    `--request-permission`), this script forwards args to `screen-record` as-is.
  - Otherwise, this script defaults to screenshot mode (adds `--screenshot`).

Options:
  --help         Show this help text.

Examples:
  screenshot.sh --list-windows
  screenshot.sh --active-window --path "$CODEX_HOME/out/screenshot.png"
  screenshot.sh --app "Terminal" --window-name "Docs" --path "$CODEX_HOME/out/terminal-docs.png"

For full flags, run:
  screen-record --help
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v screen-record >/dev/null 2>&1; then
  cat <<'MSG' >&2
error: screen-record is required

Install:
  brew install nils-cli
MSG
  exit 1
fi

os="$(uname -s 2>/dev/null || true)"
if [[ "$os" != "Darwin" && -z "${CODEX_SCREEN_RECORD_TEST_MODE:-}" ]]; then
  echo "error: screenshot skill only supports macOS (screen-record)" >&2
  exit 2
fi

args=("$@")

pass_through=0
for arg in "${args[@]}"; do
  case "$arg" in
    --list-windows|--list-apps|--preflight|--request-permission)
      pass_through=1
      break
      ;;
  esac
done

if [[ "$pass_through" == "1" ]]; then
  exec screen-record "${args[@]}"
fi

has_screenshot=0
has_selector=0
has_output=0
for arg in "${args[@]}"; do
  case "$arg" in
    --screenshot)
      has_screenshot=1
      ;;
    --window-id|--window-id=*|--app|--app=*|--active-window)
      has_selector=1
      ;;
    --path|--path=*|--dir|--dir=*)
      has_output=1
      ;;
  esac
done

final_args=()
if [[ "$has_screenshot" == "0" ]]; then
  final_args+=(--screenshot)
fi

if [[ "$has_selector" == "0" ]]; then
  final_args+=(--active-window)
fi

if [[ "$has_output" == "0" && -n "${CODEX_HOME:-}" && -d "${CODEX_HOME:-}" ]]; then
  out_dir="${CODEX_HOME}/out/screenshot"
  mkdir -p "$out_dir" 2>/dev/null || true
  final_args+=(--dir "$out_dir")
fi

final_args+=("${args[@]}")

exec screen-record "${final_args[@]}"
