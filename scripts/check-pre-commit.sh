#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/check-pre-commit.sh

Runs the local pre-commit validation gate:
  1) scripts/check.sh --all
  2) bash scripts/ci/stale-skill-scripts-audit.sh --check
  3) scripts/check.sh --entrypoint-ownership

This wrapper intentionally runs skill entrypoint checks every time to avoid
missing conditional checks when skill scripts are added/removed.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "error: unknown argument: ${1:-}" >&2
  usage >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$repo_root"

export AGENT_HOME="${AGENT_HOME:-$repo_root}"

echo "pre-commit: scripts/check.sh --all" >&2
scripts/check.sh --all

echo "pre-commit: stale skill scripts audit" >&2
bash scripts/ci/stale-skill-scripts-audit.sh --check

echo "pre-commit: skill script entrypoint ownership" >&2
scripts/check.sh --entrypoint-ownership

echo "pre-commit: all checks passed" >&2
