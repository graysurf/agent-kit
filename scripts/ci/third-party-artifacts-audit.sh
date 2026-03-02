#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/ci/third-party-artifacts-audit.sh [--strict]

Checks third-party artifact freshness and required file presence:
  - THIRD_PARTY_LICENSES.md
  - THIRD_PARTY_NOTICES.md
  - scripts/generate-third-party-artifacts.sh --check

Options:
  --strict   Treat warnings as hard failures (exit 1)
  -h, --help Show this help
USAGE
}

strict=0
while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --strict)
      strict=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: ${1:-}" >&2
      usage >&2
      exit 2
      ;;
  esac
done

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" || ! -d "$repo_root" ]]; then
  echo "error: must run inside a git work tree" >&2
  exit 2
fi
cd "$repo_root"

generator_script="scripts/generate-third-party-artifacts.sh"
required_artifacts=("THIRD_PARTY_LICENSES.md" "THIRD_PARTY_NOTICES.md")
warning_count=0

pass() {
  printf 'PASS [third-party-artifacts] %s\n' "$1"
}

warn() {
  printf 'WARN [third-party-artifacts] %s\n' "$1"
  warning_count=$((warning_count + 1))
}

fail() {
  printf 'FAIL [third-party-artifacts] %s\n' "$1" >&2
  exit 1
}

if [[ -x "$generator_script" ]]; then
  pass "generator script present: ${generator_script}"
else
  warn "missing or non-executable generator script: ${generator_script}"
fi

for artifact in "${required_artifacts[@]}"; do
  if [[ -f "$artifact" ]]; then
    pass "artifact present: ${artifact}"
  else
    warn "artifact missing: ${artifact} (run: bash scripts/generate-third-party-artifacts.sh --write)"
  fi
done

if [[ -x "$generator_script" ]]; then
  set +e
  check_output="$(bash "$generator_script" --check 2>&1)"
  check_rc=$?
  set -e

  if [[ "$check_rc" -eq 0 ]]; then
    pass "generator check passed"
  else
    warn "artifact drift detected (run: bash scripts/generate-third-party-artifacts.sh --write)"
    if [[ -n "$check_output" ]]; then
      printf '%s\n' "$check_output" >&2
    fi
  fi
fi

if [[ "$warning_count" -eq 0 ]]; then
  pass "third-party artifact audit passed (strict=${strict})"
  exit 0
fi

if [[ "$strict" -eq 1 ]]; then
  fail "strict mode treats warnings as failures"
fi

warn "third-party artifact audit completed with warnings (strict=${strict})"
exit 0
