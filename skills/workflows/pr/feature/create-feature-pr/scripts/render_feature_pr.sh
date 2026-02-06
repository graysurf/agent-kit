#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage: render_feature_pr.sh [--pr|--output] [--progress-url <url>] [--planning-pr <number>]

--pr                 Output the PR body template
--output             Output the skill output template
--progress-url <url> Include "## Progress" with a full GitHub URL (only with --pr)
--planning-pr <num>  Include "## Planning PR" as "- #<num>" (only with --pr)

Notes:
  - Optional sections are omitted when their values are not provided.
  - Never render `None` in PR body optional sections.
USAGE
}

mode=""
progress_url=""
planning_pr=""

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
    --progress-url)
      if [[ $# -lt 2 ]]; then
        echo "error: --progress-url requires a value" >&2
        usage >&2
        exit 1
      fi
      progress_url="$2"
      shift 2
      ;;
    --planning-pr)
      if [[ $# -lt 2 ]]; then
        echo "error: --planning-pr requires a value" >&2
        usage >&2
        exit 1
      fi
      planning_pr="$2"
      shift 2
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

if [[ "$mode" == "--output" ]] && ([[ -n "$progress_url" ]] || [[ -n "$planning_pr" ]]); then
  echo "error: --progress-url/--planning-pr can only be used with --pr" >&2
  usage >&2
  exit 1
fi

if [[ -n "$progress_url" ]] && [[ ! "$progress_url" =~ ^https://github\.com/[[:graph:]]+$ ]]; then
  echo "error: --progress-url must be a full GitHub URL" >&2
  exit 1
fi

if [[ -n "$planning_pr" ]]; then
  planning_pr="${planning_pr#\#}"
  if [[ ! "$planning_pr" =~ ^[1-9][0-9]*$ ]]; then
    echo "error: --planning-pr must be a positive PR number" >&2
    exit 1
  fi
fi

render_optional_sections() {
  if [[ -n "$progress_url" ]]; then
    cat <<EOF
## Progress
- [docs/progress/<YYYYMMDD_feature_slug>.md](${progress_url})

EOF
  fi

  if [[ -n "$planning_pr" ]]; then
    cat <<EOF
## Planning PR
- #${planning_pr}

EOF
  fi
}

render_pr_template() {
  local template=''
  local optional_sections=''
  template="$(cat "${skill_dir}/references/PR_TEMPLATE.md")"
  optional_sections="$(render_optional_sections)"
  printf '%s\n' "${template//'{{OPTIONAL_SECTIONS}}'/$optional_sections}"
}

case "$mode" in
  --pr)
    render_pr_template
    ;;
  --output)
    cat "${skill_dir}/references/ASSISTANT_RESPONSE_TEMPLATE.md"
    ;;
  *)
    echo "error: unknown mode: $mode" >&2
    exit 1
    ;;
esac
