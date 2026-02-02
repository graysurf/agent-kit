#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  screenshot.sh [--preflight] [--help] [--] <args...>

Delegates to the cross-platform Python helper on macOS/Linux.
On Windows, run the PowerShell helper directly.

Options:
  --preflight    Run macOS Screen Recording permission helper before capture.
  --help         Show this help text.

Examples:
  screenshot.sh --mode temp
  screenshot.sh --preflight --app "Codex"
  screenshot.sh --path "$CODEX_HOME/out/screenshot.png"

Pass-through arguments are forwarded to scripts/take_screenshot.py.
USAGE
}

preflight=0
pass_args=()

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    -h|--help)
      usage
      exit 0
      ;;
    --preflight)
      preflight=1
      shift
      ;;
    --)
      shift
      pass_args+=("$@")
      break
      ;;
    *)
      pass_args+=("${1:-}")
      shift
      ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python_helper="$script_dir/take_screenshot.py"

os="$(uname -s 2>/dev/null || true)"
case "$os" in
  Darwin)
    platform="macos"
    ;;
  Linux)
    platform="linux"
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    platform="windows"
    ;;
  *)
    platform="unknown"
    ;;
esac

if [[ "$platform" == "windows" ]]; then
  cat <<'MSG' >&2
Windows detected. Run the PowerShell helper instead:
  powershell -ExecutionPolicy Bypass -File scripts/take_screenshot.ps1
MSG
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required" >&2
  exit 1
fi

if [[ "$platform" == "macos" && "$preflight" == "1" ]]; then
  "$script_dir/ensure_macos_permissions.sh"
fi

exec python3 "$python_helper" "${pass_args[@]}"
