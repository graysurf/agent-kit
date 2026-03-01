#!/usr/bin/env bash
set -euo pipefail

print_help() {
  printf '%s\n' \
    "agent-browser CLI wrapper" \
    "" \
    "Usage:" \
    "  agent-browser.sh [--session <name>] <command> [args...]" \
    "" \
    "Environment:" \
    "  AGENT_BROWSER_CLI_SESSION  Default session name (used when --session is not passed)" \
    "" \
    "Notes:" \
    "  - This wrapper runs the Agent Browser CLI via npx:" \
    "      npx --yes --package agent-browser@latest agent-browser ..." \
    "  - '--help' / '-h' is handled locally (no network / Node required)."
}

case "${1:-}" in
  ""|--help|-h)
    print_help
    exit 0
    ;;
esac

if ! command -v npx >/dev/null 2>&1; then
  echo "Error: npx is required but not found on PATH." >&2
  exit 1
fi

has_session_flag=0
for arg in "$@"; do
  case "$arg" in
    --session|--session=*)
      has_session_flag=1
      break
      ;;
  esac
done

cmd=(npx --yes --package agent-browser@latest agent-browser)
if [[ ${has_session_flag} -eq 0 && -n "${AGENT_BROWSER_CLI_SESSION:-}" ]]; then
  cmd+=(--session "${AGENT_BROWSER_CLI_SESSION}")
fi
cmd+=("$@")

exec "${cmd[@]}"
