#!/usr/bin/env bash

check_semgrep_summary() {
  local json_path="${1:-}"
  local limit="${CHECK_SEMGREP_SUMMARY_LIMIT:-5}"
  local repo_root="${CHECK_REPO_ROOT:-}"
  local python_bin="${repo_root}/.venv/bin/python"

  if [[ -z "$json_path" ]]; then
    return 0
  fi

  if [[ ! -x "$python_bin" ]]; then
    python_bin="$(command -v python3 || true)"
  fi
  if [[ -z "$python_bin" ]]; then
    echo "warning: python3 not found; skipping semgrep summary" >&2
    return 0
  fi

  "$python_bin" - "$json_path" "$limit" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    limit = int(sys.argv[2])
except Exception:
    limit = 5

try:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except Exception as exc:
    sys.stderr.write(f"semgrep: failed to read {path}: {exc}\n")
    sys.exit(0)

results = data.get("results") or []
count = len(results)
if count == 0:
    sys.stderr.write("semgrep: 0 findings\n")
    sys.exit(0)

sys.stderr.write(f"semgrep: {count} findings (showing up to {limit})\n")
for result in results[:limit]:
    check_id = result.get("check_id") or "unknown"
    path = result.get("path") or "unknown"
    start = result.get("start") or {}
    line = start.get("line")
    location = f"{path}:{line}" if line else path
    message = (result.get("extra") or {}).get("message") or ""
    message = " ".join(message.split())
    if message:
        sys.stderr.write(f"- {check_id} {location} {message}\n")
    else:
        sys.stderr.write(f"- {check_id} {location}\n")
PY
}

check_run_selected() {
  local lint_rc=0
  local markdown_rc=0
  local third_party_rc=0
  local contract_rc=0
  local skill_layout_rc=0
  local env_bools_rc=0
  local docs_rc=0
  local semgrep_rc=0
  local stale_skill_audit_rc=0
  local entrypoint_ownership_rc=0
  local test_rc=0

  if [[ "$CHECK_RUN_LINT" -eq 1 || "$CHECK_RUN_LINT_SHELL" -eq 1 || "$CHECK_RUN_LINT_PYTHON" -eq 1 ]]; then
    local -a lint_args=()
    if [[ "$CHECK_RUN_LINT" -eq 1 || ( "$CHECK_RUN_LINT_SHELL" -eq 1 && "$CHECK_RUN_LINT_PYTHON" -eq 1 ) ]]; then
      lint_args=(all)
    elif [[ "$CHECK_RUN_LINT_SHELL" -eq 1 ]]; then
      lint_args=(shell)
    elif [[ "$CHECK_RUN_LINT_PYTHON" -eq 1 ]]; then
      lint_args=(python)
    fi

    set +e
    scripts/lint.sh "${lint_args[@]}"
    lint_rc=$?
    set -e
    if [[ "$lint_rc" -ne 0 ]]; then
      echo "error: lint failed (exit=$lint_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_MARKDOWN" -eq 1 ]]; then
    echo "lint: markdown" >&2
    set +e
    bash scripts/ci/markdownlint-audit.sh --strict
    markdown_rc=$?
    set -e
    if [[ "$markdown_rc" -ne 0 ]]; then
      echo "error: markdown lint failed (exit=$markdown_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_THIRD_PARTY" -eq 1 ]]; then
    echo "lint: third-party artifacts audit" >&2
    set +e
    bash scripts/ci/third-party-artifacts-audit.sh --strict
    third_party_rc=$?
    set -e
    if [[ "$third_party_rc" -ne 0 ]]; then
      echo "error: third-party artifacts audit failed (exit=$third_party_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_CONTRACTS" -eq 1 ]]; then
    echo "lint: validate skill contracts" >&2
    set +e
    "${AGENT_HOME}/skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh"
    contract_rc=$?
    set -e
    if [[ "$contract_rc" -ne 0 ]]; then
      echo "error: validate_skill_contracts failed (exit=$contract_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_SKILL_LAYOUT" -eq 1 ]]; then
    echo "lint: audit skill layout" >&2
    set +e
    "${AGENT_HOME}/skills/tools/skill-management/skill-governance/scripts/audit-skill-layout.sh"
    skill_layout_rc=$?
    set -e
    if [[ "$skill_layout_rc" -ne 0 ]]; then
      echo "error: audit-skill-layout failed (exit=$skill_layout_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_ENV_BOOLS" -eq 1 ]]; then
    echo "lint: env bools audit" >&2
    set +e
    zsh -f scripts/audit-env-bools.zsh --check
    env_bools_rc=$?
    set -e
    if [[ "$env_bools_rc" -ne 0 ]]; then
      echo "error: env bools audit failed (exit=$env_bools_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_DOCS" -eq 1 ]]; then
    echo "lint: docs freshness audit" >&2
    set +e
    if [[ ! -f scripts/ci/docs-freshness-audit.sh ]]; then
      echo "error: docs freshness helper is missing (expected scripts/ci/docs-freshness-audit.sh)" >&2
      docs_rc=1
    else
      bash scripts/ci/docs-freshness-audit.sh --check
      docs_rc=$?
    fi
    set -e
    if [[ "$docs_rc" -ne 0 ]]; then
      echo "error: docs freshness audit failed (exit=$docs_rc)" >&2
      echo "hint: run 'bash scripts/ci/docs-freshness-audit.sh --check' and fix stale docs command/path references or rules coverage" >&2
    fi
  fi

  if [[ "$CHECK_RUN_SEMGREP" -eq 1 ]]; then
    echo "lint: semgrep scan" >&2
    set +e
    local semgrep_json=''
    semgrep_json="$(scripts/semgrep-scan.sh)"
    semgrep_rc=$?
    set -e
    if [[ "$semgrep_rc" -ne 0 ]]; then
      echo "error: semgrep scan failed (exit=$semgrep_rc)" >&2
    else
      if [[ -n "$semgrep_json" ]]; then
        printf '%s\n' "$semgrep_json"
      fi
      check_semgrep_summary "$semgrep_json"
    fi
  fi

  if [[ "$CHECK_RUN_STALE_SKILL_AUDIT" -eq 1 ]]; then
    echo "lint: stale skill scripts audit" >&2
    set +e
    bash scripts/ci/stale-skill-scripts-audit.sh --check
    stale_skill_audit_rc=$?
    set -e
    if [[ "$stale_skill_audit_rc" -ne 0 ]]; then
      echo "error: stale skill scripts audit failed (exit=$stale_skill_audit_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_ENTRYPOINT_OWNERSHIP" -eq 1 ]]; then
    echo "tests: skill script entrypoint ownership" >&2
    set +e
    scripts/test.sh -k entrypoint_ownership
    entrypoint_ownership_rc=$?
    set -e
    if [[ "$entrypoint_ownership_rc" -ne 0 ]]; then
      echo "error: entrypoint ownership tests failed (exit=$entrypoint_ownership_rc)" >&2
    fi
  fi

  if [[ "$CHECK_RUN_TESTS" -eq 1 ]]; then
    set +e
    if [[ "${#CHECK_PYTEST_ARGS[@]}" -gt 0 ]]; then
      scripts/test.sh "${CHECK_PYTEST_ARGS[@]}"
    else
      scripts/test.sh
    fi
    test_rc=$?
    set -e
    if [[ "$test_rc" -ne 0 ]]; then
      echo "error: pytest failed (exit=$test_rc)" >&2
    fi
  fi

  if [[ "$lint_rc" -ne 0 || "$markdown_rc" -ne 0 || "$third_party_rc" -ne 0 || "$contract_rc" -ne 0 || "$skill_layout_rc" -ne 0 || "$env_bools_rc" -ne 0 || "$docs_rc" -ne 0 || "$semgrep_rc" -ne 0 || "$stale_skill_audit_rc" -ne 0 || "$entrypoint_ownership_rc" -ne 0 || "$test_rc" -ne 0 ]]; then
    return 1
  fi

  return 0
}
