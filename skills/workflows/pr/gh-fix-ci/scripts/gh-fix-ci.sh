#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  gh-fix-ci.sh [--repo <path>] [--pr <number|url>] [--max-lines <n>] [--context <n>] [--json]

Runs the bundled inspect_pr_checks.py to fetch failing PR checks and log snippets.

Examples:
  gh-fix-ci.sh --pr 123
  gh-fix-ci.sh --repo . --pr https://github.com/org/repo/pull/123 --json

Notes:
  Requires gh authentication. Run `gh auth status` first.
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/inspect_pr_checks.py" "$@"
