#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"
shared_refs_default="$(cd "${skill_dir}/../../../../automation/find-and-fix-bugs/references" && pwd)"

resolve_shared_refs_dir() {
  if [[ -n "${AGENT_HOME:-}" ]] && [[ -d "${AGENT_HOME%/}/skills/automation/find-and-fix-bugs/references" ]]; then
    printf '%s\n' "${AGENT_HOME%/}/skills/automation/find-and-fix-bugs/references"
    return 0
  fi

  printf '%s\n' "${shared_refs_default}"
}

usage() {
  cat <<'USAGE'
Usage: render_bug_pr.sh [--pr|--output]

--pr                 Output the shared bug PR body template
--output             Output the shared assistant response template
USAGE
}

mode=""

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --pr|--output)
      if [[ -n "$mode" ]]; then
        echo "error: choose exactly one mode" >&2
        usage >&2
        exit 1
      fi
      mode="$1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: ${1}" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$mode" ]]; then
  usage >&2
  exit 1
fi

shared_refs_dir="$(resolve_shared_refs_dir)"
pr_template="${shared_refs_dir}/PR_TEMPLATE.md"
output_template="${shared_refs_dir}/ASSISTANT_RESPONSE_TEMPLATE.md"

if [[ ! -f "$pr_template" ]]; then
  echo "error: missing shared PR template: $pr_template" >&2
  exit 1
fi
if [[ ! -f "$output_template" ]]; then
  echo "error: missing shared output template: $output_template" >&2
  exit 1
fi

case "$mode" in
  --pr)
    cat "$pr_template"
    ;;
  --output)
    cat "$output_template"
    ;;
  *)
    echo "error: unknown mode: $mode" >&2
    exit 1
    ;;
esac
