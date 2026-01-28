#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  validate_skill_contracts.sh [--file <path>]...

Validates that each SKILL.md contains a `## Contract` section with the required
headings in exact order:
  Prereqs:
  Inputs:
  Outputs:
  Exit codes:
  Failure modes:

Notes:
  - By default, checks all `skills/**/SKILL.md` files in the current git repo.
  - `--file` may be repeated to validate specific files (useful for smoke tests).
  - The heading check is scoped to the `## Contract` section only (until the next `## ` heading or EOF).
USAGE
}

files=()

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --file)
      if [[ $# -lt 2 ]]; then
        echo "error: --file requires a path" >&2
        usage >&2
        exit 1
      fi
      files+=("${2:-}")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: ${1}" >&2
      usage >&2
      exit 1
      ;;
  esac
done

for cmd in git python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "error: $cmd is required" >&2
    exit 1
  fi
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "error: must run inside a git work tree" >&2
  exit 1
}

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ ${#files[@]} -eq 0 ]]; then
  mapfile -t files < <(git ls-files -- 'skills/**/SKILL.md' | LC_ALL=C sort)
fi

python3 - "${files[@]}" <<'PY'
import sys
from pathlib import Path

required = ["Prereqs:", "Inputs:", "Outputs:", "Exit codes:", "Failure modes:"]
MAX_PREAMBLE_NONEMPTY = 2

def die(msg: str) -> None:
  print(f"error: {msg}", file=sys.stderr)

def check_file_structure(raw: list[str]) -> list[str]:
  problems: list[str] = []

  h1_idx: int | None = None
  for i, line in enumerate(raw):
    if line.startswith("# "):
      h1_idx = i
      break
  if h1_idx is None:
    problems.append("missing H1 title (`# <Title>`)")
    return problems

  contract_idx: int | None = None
  for i, line in enumerate(raw):
    if line.strip() == "## Contract":
      contract_idx = i
      break
  if contract_idx is None:
    problems.append("missing ## Contract")
    return problems

  if contract_idx <= h1_idx:
    problems.append("`## Contract` must appear after the H1 title")
    return problems

  # Contract must be the first H2 after H1.
  first_h2_idx: int | None = None
  for i in range(h1_idx + 1, len(raw)):
    if raw[i].startswith("## "):
      first_h2_idx = i
      break
  if first_h2_idx is not None and first_h2_idx != contract_idx:
    first_h2 = raw[first_h2_idx].strip()
    problems.append(f"`## Contract` must be the first H2 (found {first_h2!r} first)")

  # Preamble: allow up to MAX_PREAMBLE_NONEMPTY non-empty lines between H1 and Contract.
  preamble = raw[h1_idx + 1 : contract_idx]
  preamble_nonempty = [line for line in preamble if line.strip()]
  if len(preamble_nonempty) > MAX_PREAMBLE_NONEMPTY:
    problems.append(
      f"preamble too long before `## Contract` ({len(preamble_nonempty)} non-empty lines; max {MAX_PREAMBLE_NONEMPTY})"
    )

  # Disallow any headings before Contract other than the first H1.
  in_fence = False
  for line in preamble:
    stripped = line.lstrip()
    if stripped.startswith("```"):
      in_fence = not in_fence
      continue
    if in_fence:
      continue
    if stripped.startswith("#"):
      hashes = 0
      for ch in stripped:
        if ch == "#":
          hashes += 1
          continue
        break
      if 1 <= hashes <= 6 and len(stripped) > hashes and stripped[hashes] == " ":
        problems.append("markdown heading found before `## Contract` (move it after the Contract)")
        break

  return problems


def check_contract_headings(raw: list[str]) -> list[str]:
  try:
    start = next(i for i, line in enumerate(raw) if line.strip() == "## Contract")
  except StopIteration:
    return ["missing ## Contract"]

  end = len(raw)
  for i in range(start + 1, len(raw)):
    line = raw[i]
    if line.startswith("## ") and line.strip() != "## Contract":
      end = i
      break

  block = [line.strip() for line in raw[start + 1 : end]]
  problems: list[str] = []
  last_idx = -1
  for h in required:
    try:
      idx = block.index(h)
    except ValueError:
      problems.append(f"missing {h}")
      continue
    if idx <= last_idx:
      problems.append(f"out of order {h}")
    last_idx = idx
  return problems

paths = [Path(p) for p in sys.argv[1:]]
if not paths:
  die("no files to validate")
  raise SystemExit(1)

errors: list[str] = []
for p in paths:
  if not p.is_file():
    errors.append(f"{p}: file not found")
    continue

  raw_lines = p.read_text("utf-8", errors="replace").splitlines()
  problems: list[str] = []
  structure = check_file_structure(raw_lines)
  problems.extend(structure)
  if "missing ## Contract" not in structure:
    problems.extend(check_contract_headings(raw_lines))

  # De-duplicate problems while preserving order for stable output.
  seen: set[str] = set()
  uniq: list[str] = []
  for item in problems:
    if item in seen:
      continue
    seen.add(item)
    uniq.append(item)
  problems = uniq
  if not problems:
    continue

  missing = [x for x in problems if x.startswith("missing ")]
  order = [x for x in problems if x.startswith("out of order ")]
  other = [x for x in problems if x not in missing and x not in order]

  if missing:
    errors.append(f"{p}: {', '.join(missing)}")
  if order:
    errors.append(
      f"{p}: headings out of order in ## Contract (expected: {', '.join(required)})"
    )
  if other:
    errors.append(f"{p}: {'; '.join(other)}")

if errors:
  for e in errors:
    die(e)
  raise SystemExit(1)
PY
