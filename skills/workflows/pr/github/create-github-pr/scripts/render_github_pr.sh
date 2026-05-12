#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage: render_github_pr.sh --kind <feature|bug> [--pr|--output]

--kind <feature|bug>  Select the GitHub PR kind
--pr                  Output the PR body template
--output              Output the skill output template
USAGE
}

kind=""
mode=""

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --kind)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "error: --kind requires a value" >&2
        usage >&2
        exit 1
      fi
      kind="$2"
      shift 2
      ;;
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

if [[ -z "$kind" ]]; then
  echo "error: --kind is required" >&2
  usage >&2
  exit 1
fi

case "$kind" in
  feature|bug)
    ;;
  *)
    echo "error: unsupported kind: $kind" >&2
    usage >&2
    exit 1
    ;;
esac

if [[ -z "$mode" ]]; then
  echo "error: choose exactly one mode" >&2
  usage >&2
  exit 1
fi

render_template() {
  local template_path="$1"
  local template=''
  template="$(cat "$template_path")"
  printf '%s\n' "${template//'{{OPTIONAL_SECTIONS}}'/}"
}

case "$kind:$mode" in
  feature:--pr)
    render_template "${skill_dir}/references/FEATURE_PR_TEMPLATE.md"
    ;;
  feature:--output)
    cat "${skill_dir}/references/FEATURE_ASSISTANT_RESPONSE_TEMPLATE.md"
    ;;
  bug:--pr)
    render_template "${skill_dir}/references/BUG_PR_TEMPLATE.md"
    ;;
  bug:--output)
    cat "${skill_dir}/references/BUG_ASSISTANT_RESPONSE_TEMPLATE.md"
    ;;
  *)
    echo "error: unknown mode: $mode" >&2
    exit 1
    ;;
esac
