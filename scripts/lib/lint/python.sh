#!/usr/bin/env bash

lint_run_python() {
  echo "lint: python (ruff/mypy/pyright)" >&2

  local repo_root="${LINT_REPO_ROOT:-}"
  if [[ -z "$repo_root" ]]; then
    echo "error: LINT_REPO_ROOT is not set" >&2
    return 2
  fi

  local rc=0
  local uv_bin=''
  uv_bin="$(command -v uv || true)"
  if [[ -z "$uv_bin" ]]; then
    echo "error: uv not found; install uv and run: uv sync --locked" >&2
    return 1
  fi

  local python_bin=''
  python_bin="$("$uv_bin" run --locked python -c 'import sys; print(sys.executable)')" || return 1

  echo "lint: ruff check" >&2
  set +e
  "$uv_bin" run --locked ruff check --output-format concise tests
  local ruff_rc=$?
  set -e
  if [[ "$ruff_rc" -ne 0 ]]; then
    rc=1
  fi

  echo "lint: mypy" >&2
  local mypy_cfg="${repo_root}/mypy.ini"
  set +e
  if [[ -f "$mypy_cfg" ]]; then
    "$uv_bin" run --locked mypy --no-color-output --config-file "$mypy_cfg" tests
  else
    "$uv_bin" run --locked mypy --no-color-output tests
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
    "$uv_bin" run --locked pyright --warnings --pythonpath "$python_bin" --project "$pyright_cfg"
  else
    "$uv_bin" run --locked pyright --warnings --pythonpath "$python_bin" tests
  fi
  local pyright_rc=$?
  set -e
  if [[ "$pyright_rc" -ne 0 ]]; then
    rc=1
  fi

  echo "lint: python -c compile()" >&2
  set +e
  PYTHONDONTWRITEBYTECODE=1 "$uv_bin" run --locked python - <<'PY'
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
