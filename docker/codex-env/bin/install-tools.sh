#!/usr/bin/env bash
set -euo pipefail

zsh_kit_dir="${ZSH_KIT_DIR:-/opt/zsh-kit}"
required_list="${zsh_kit_dir%/}/config/tools.list"
optional_list="${zsh_kit_dir%/}/config/tools.optional.list"

install_optional_tools="${INSTALL_OPTIONAL_TOOLS:-1}"
install_vscode="${INSTALL_VSCODE:-1}"

if [[ ! -f "$required_list" ]]; then
  echo "error: tools.list not found: $required_list" >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "error: brew not found on PATH" >&2
  exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "error: sudo not found on PATH" >&2
  exit 1
fi

export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_INSTALL_CLEANUP=1

install_code_via_apt() {
  if [[ "$install_vscode" != "1" ]]; then
    echo "skip: vscode (INSTALL_VSCODE != 1)" >&2
    return 0
  fi

  sudo apt-get update -y >/dev/null

  if command -v code >/dev/null 2>&1; then
    return 0
  fi

  sudo install -d -m 0755 /etc/apt/keyrings
  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /etc/apt/keyrings/packages.microsoft.gpg >/dev/null
  sudo chmod 0644 /etc/apt/keyrings/packages.microsoft.gpg

  local arch
  arch="$(dpkg --print-architecture)"
  echo "deb [arch=${arch} signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" \
    | sudo tee /etc/apt/sources.list.d/vscode.list >/dev/null

  sudo apt-get update -y
  sudo apt-get install -y code

  code --version >/dev/null
}

install_mitmproxy_via_apt() {
  sudo apt-get update -y >/dev/null
  sudo apt-get install -y mitmproxy
  mitmproxy --version >/dev/null
}

entries_tsv="$(python3 - "$required_list" "$optional_list" "$install_optional_tools" <<'PY'
import sys
from pathlib import Path

required, optional, include_optional = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] == "1"

def iter_entries(path: Path, source: str):
  if not path.exists():
    return
  for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
      continue
    parts = raw.split("::")
    tool = (parts[0] or "").strip()
    brew_name = (parts[1] if len(parts) >= 2 else "").strip() or tool
    if not tool:
      continue
    yield tool, brew_name, source

seen = set()
def emit(entries):
  for t, b, s in entries:
    if t in seen:
      continue
    seen.add(t)
    print(f"{t}\t{b}\t{s}")

if include_optional:
  emit(iter_entries(required, "required"))
  emit(iter_entries(optional, "optional"))
else:
  emit(iter_entries(required, "required"))
PY
)"

missing_required=0
missing_optional=0

while IFS=$'\t' read -r tool brew_name source; do
  [[ -z "${tool:-}" ]] && continue

  case "$tool" in
    code)
      if brew install "$brew_name"; then
        if command -v code >/dev/null 2>&1; then
          continue
        fi
      fi
      install_code_via_apt
      continue
      ;;
    mitmproxy)
      install_mitmproxy_via_apt
      continue
      ;;
  esac

  if brew install "$brew_name"; then
    continue
  fi

  echo "warn: failed to install via brew: tool=$tool brew_name=$brew_name source=$source" >&2
  if [[ "$source" == "required" ]]; then
    missing_required=1
  else
    missing_optional=1
  fi
done <<<"$entries_tsv"

if (( missing_required )); then
  echo "error: missing required tools (see warnings above)" >&2
  exit 1
fi

if (( missing_optional )); then
  echo "warning: missing optional tools (see warnings above)" >&2
fi
