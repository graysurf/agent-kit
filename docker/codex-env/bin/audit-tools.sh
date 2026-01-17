#!/usr/bin/env bash
set -euo pipefail

zsh_kit_dir="${ZSH_KIT_DIR:-/opt/zsh-kit}"
required_list="${zsh_kit_dir%/}/config/tools.list"
optional_list="${zsh_kit_dir%/}/config/tools.optional.list"

if [[ ! -f "$required_list" ]]; then
  echo "error: tools.list not found: $required_list" >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "error: brew not found on PATH" >&2
  exit 1
fi

python3 - "$required_list" "$optional_list" <<'PY' | while IFS=$'\t' read -r tool brew_name source; do
import sys
from pathlib import Path

required, optional = Path(sys.argv[1]), Path(sys.argv[2])

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

for t, b, s in iter_entries(required, "required"):
  print(f"{t}\t{b}\t{s}")
for t, b, s in iter_entries(optional, "optional"):
  print(f"{t}\t{b}\t{s}")
PY
  [[ -z "${tool:-}" ]] && continue

  set +e
  out="$(brew install -n "$brew_name" 2>&1)"
  rc=$?
  set -e

  status="brew:fail"
  notes="$(echo "$out" | head -n 1 | tr '\t' ' ')"

  if [[ $rc -eq 0 ]]; then
    if echo "$out" | grep -qi "Would install .*cask"; then
      status="brew:cask-dryrun"
    else
      status="brew:ok-dryrun"
    fi
    notes="ok"
  fi

  printf "%s\t%s\t%s\t%s\t%s\n" "$tool" "$brew_name" "$source" "$status" "$notes"
done

