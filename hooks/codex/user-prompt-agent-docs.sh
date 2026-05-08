#!/usr/bin/env bash
#
# UserPromptSubmit hook: inject a lightweight agent-docs preflight reminder
# when a prompt looks like implementation work inside a repo with AGENTS.md.
#
set -uo pipefail

if [[ "${AGENT_KIT_SUPPRESS_PREFLIGHT:-0}" == "1" ]]; then
  exit 0
fi

command -v git >/dev/null 2>&1 || exit 0
python_bin="$(command -v python3 || true)"
[[ -z "$python_bin" ]] && exit 0

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "$repo_root" ]] && exit 0
[[ -f "$repo_root/AGENTS.md" ]] || exit 0

payload="$(cat)"
prompt="$(
  "$python_bin" -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}

for key in ("prompt", "user_prompt", "message", "input"):
    value = payload.get(key) if isinstance(payload, dict) else None
    if isinstance(value, str):
        print(value)
        break
' <<< "$payload" 2>/dev/null || true
)"
[[ -z "$prompt" ]] && exit 0

lc_prompt="$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')"
case "$lc_prompt" in
  *'agent-docs'*) exit 0 ;;
esac

matched=0
wb_keywords='implement|implementing|refactor|refactoring|rewrite|rewriting'
wb_keywords+='|scaffold|scaffolding|integrate|integrating'
wb_keywords+='|migrate|migration|migrating|optimize|optimise|optimizing|optimising'
if printf '%s' "$lc_prompt" | grep -qwE "$wb_keywords"; then
  matched=1
fi

if [[ "$matched" -eq 0 ]]; then
  for phrase in \
    'add a test' 'add the test' 'add tests' 'add new test' 'add more test' \
    'write a test' 'write the test' 'write tests' 'write new test' \
    'build a ' 'build an ' 'build the ' \
    'create a ' 'create an ' 'create the ' \
    'add a feature' 'add the feature' 'add new feature' \
    'fix the bug' 'fix this bug' 'fix a bug' \
    'hook up ' 'wire up '; do
    case "$lc_prompt" in
      *"$phrase"*) matched=1; break ;;
    esac
  done
fi

[[ "$matched" -eq 0 ]] && exit 0

agent_home="${AGENT_HOME:-$HOME/.agents}"
reminder="[agent-kit] This repo has AGENTS.md. Before implementation edits, run the agent-docs preflight:
  agent-docs --docs-home \"\$AGENT_HOME\" resolve --context startup --strict --format checklist
  agent-docs --docs-home \"\$AGENT_HOME\" resolve --context project-dev --strict --format checklist
Use AGENT_HOME=${agent_home} if it is not already exported. Proceed with writes only when required docs report status=present."

CTX="$reminder" "$python_bin" -c '
import json
import os

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": os.environ["CTX"],
    }
}))
'
