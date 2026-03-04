#!/usr/bin/env bash

lint_run_python() {
  echo "lint: python (ruff/mypy/pyright)" >&2

  local repo_root="${LINT_REPO_ROOT:-}"
  if [[ -z "$repo_root" ]]; then
    echo "error: LINT_REPO_ROOT is not set" >&2
    return 2
  fi

  local rc=0
  local python_bin="${repo_root}/.venv/bin/python"
  if [[ ! -x "$python_bin" ]]; then
    python_bin="$(command -v python3 || true)"
  fi
  if [[ -z "$python_bin" ]]; then
    echo "error: python3 not found; create a venv at .venv/ and install requirements-dev.txt" >&2
    return 1
  fi

  local ruff_bin="${repo_root}/.venv/bin/ruff"
  if [[ ! -x "$ruff_bin" ]]; then
    ruff_bin="$(command -v ruff || true)"
  fi
  if [[ -z "$ruff_bin" ]]; then
    echo "error: ruff not found" >&2
    echo "hint: run: .venv/bin/pip install -r requirements-dev.txt" >&2
    return 1
  fi

  local mypy_bin="${repo_root}/.venv/bin/mypy"
  if [[ ! -x "$mypy_bin" ]]; then
    mypy_bin="$(command -v mypy || true)"
  fi
  if [[ -z "$mypy_bin" ]]; then
    echo "error: mypy not found" >&2
    echo "hint: run: .venv/bin/pip install -r requirements-dev.txt" >&2
    return 1
  fi

  local pyright_bin="${repo_root}/.venv/bin/pyright"
  if [[ ! -x "$pyright_bin" ]]; then
    pyright_bin="$(command -v pyright || true)"
  fi
  if [[ -z "$pyright_bin" ]]; then
    echo "error: pyright not found" >&2
    echo "hint: run: .venv/bin/pip install -r requirements-dev.txt" >&2
    return 1
  fi

  echo "lint: ruff check" >&2
  set +e
  "$ruff_bin" check --output-format concise tests
  local ruff_rc=$?
  set -e
  if [[ "$ruff_rc" -ne 0 ]]; then
    rc=1
  fi

  echo "lint: mypy" >&2
  local mypy_cfg="${repo_root}/mypy.ini"
  set +e
  if [[ -f "$mypy_cfg" ]]; then
    "$mypy_bin" --no-color-output --config-file "$mypy_cfg" tests
  else
    "$mypy_bin" --no-color-output tests
  fi
  local mypy_rc=$?
  set -e
  if [[ "$mypy_rc" -ne 0 ]]; then
    rc=1
  fi

  echo "lint: pyright" >&2
  local pyright_cfg="${repo_root}/pyrightconfig.json"
  set +e
  if [[ -f "$pyright_cfg" ]]; then
    "$pyright_bin" --warnings --pythonpath "$python_bin" --project "$pyright_cfg"
  else
    "$pyright_bin" --warnings --pythonpath "$python_bin" tests
  fi
  local pyright_rc=$?
  set -e
  if [[ "$pyright_rc" -ne 0 ]]; then
    rc=1
  fi

  echo "lint: python -c compile()" >&2
  set +e
  PYTHONDONTWRITEBYTECODE=1 "$python_bin" - <<'PY'
import subprocess
import sys
from pathlib import Path

tracked = subprocess.check_output(["git", "ls-files", "*.py"], text=True).splitlines()
errors = 0
for p in tracked:
  path = Path(p)
  if not path.is_file():
    continue
  try:
    src = path.read_text("utf-8")
  except Exception as exc:
    print(f"error: failed to read {p}: {exc}", file=sys.stderr)
    errors += 1
    continue
  try:
    compile(src, p, "exec")
  except SyntaxError as exc:
    print(f"error: python syntax error: {p}:{exc.lineno}:{exc.offset}: {exc.msg}", file=sys.stderr)
    errors += 1
if errors:
  raise SystemExit(1)
PY
  local py_compile_rc=$?
  set -e
  if [[ "$py_compile_rc" -ne 0 ]]; then
    rc=1
  fi

  return "$rc"
}
