#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage: render_gitlab_mr.sh [--mr|--output]

--mr                 Output the MR body template
--output             Output the skill output template
USAGE
}

mode=""

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --mr|--output)
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

case "$mode" in
  --mr)
    cat "${skill_dir}/references/MR_TEMPLATE.md"
    ;;
  --output)
    cat "${skill_dir}/references/ASSISTANT_RESPONSE_TEMPLATE.md"
    ;;
  *)
    echo "error: unknown mode: $mode" >&2
    exit 1
    ;;
esac
