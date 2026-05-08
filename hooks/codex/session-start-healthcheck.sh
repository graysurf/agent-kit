#!/usr/bin/env bash
#
# SessionStart hook: surface agent-kit baseline issues once per day.
#
set -uo pipefail

if [[ "${AGENT_KIT_SUPPRESS_HEALTH:-0}" == "1" ]]; then
  exit 0
fi

command -v agent-docs >/dev/null 2>&1 || exit 0
python_bin="$(command -v python3 || true)"
[[ -z "$python_bin" ]] && exit 0

agent_home="${AGENT_HOME:-$HOME/.agents}"
stamp_dir="$HOME/.cache/agent-kit"
stamp="$stamp_dir/health-$(date +%Y%m%d).stamp"
[[ -f "$stamp" ]] && exit 0

baseline_output="$(
  agent-docs --docs-home "$agent_home" baseline --check --target all --strict --format text 2>&1 || true
)"
[[ -z "$baseline_output" ]] && exit 0

mkdir -p "$stamp_dir"
: > "$stamp"

if ! printf '%s\n' "$baseline_output" | grep -Eq '^missing_required: [1-9][0-9]*'; then
  exit 0
fi

context="[agent-kit health]
Required baseline docs are missing in the current workspace:

${baseline_output}"

CTX="$context" "$python_bin" -c '
import json
import os

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": os.environ["CTX"],
    }
}))
'
