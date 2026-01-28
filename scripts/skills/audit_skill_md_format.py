#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


MAX_PREAMBLE_DEFAULT = 2


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def repo_root() -> Path:
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    except Exception:
        return Path.cwd().resolve()
    return Path(root).resolve()


def tracked_skill_mds(root: Path) -> list[Path]:
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--", "skills/**/SKILL.md"],
            cwd=root,
            text=True,
        )
        paths = [root / line.strip() for line in out.splitlines() if line.strip()]
        return sorted([p for p in paths if p.is_file()], key=lambda p: p.as_posix())
    except Exception:
        return sorted([p for p in (root / "skills").rglob("SKILL.md") if p.is_file()], key=lambda p: p.as_posix())


@dataclass(frozen=True)
class Violation:
    kind: str
    message: str


@dataclass(frozen=True)
class FileResult:
    path: str
    ok: bool
    max_preamble_lines: int
    preamble_nonempty_lines: int | None
    contract_line: int | None
    violations: list[Violation]
    has_setup: bool


def is_heading(line: str) -> bool:
    s = line.lstrip()
    if not s.startswith("#"):
        return False
    hashes = 0
    for ch in s:
        if ch == "#":
            hashes += 1
            continue
        break
    return 1 <= hashes <= 6 and len(s) > hashes and s[hashes] == " "


def is_h1(line: str) -> bool:
    return line.startswith("# ")


def is_h2(line: str) -> bool:
    return line.startswith("## ")


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def audit_file(path: Path, root: Path, max_preamble_lines: int) -> FileResult:
    display = display_path(path, root)
    raw = path.read_text("utf-8", errors="replace").splitlines()

    h1_idx: int | None = None
    for i, line in enumerate(raw):
        if is_h1(line):
            h1_idx = i
            break

    violations: list[Violation] = []
    if h1_idx is None:
        violations.append(Violation("missing_h1", "missing H1 title (`# <Title>`)"))
        return FileResult(
            path=display,
            ok=False,
            max_preamble_lines=max_preamble_lines,
            preamble_nonempty_lines=None,
            contract_line=None,
            violations=violations,
            has_setup=False,
        )

    contract_idx: int | None = None
    for i in range(h1_idx + 1, len(raw)):
        if raw[i].strip() == "## Contract":
            contract_idx = i
            break

    has_setup = any(line.strip() == "## Setup" for line in raw)

    if contract_idx is None:
        violations.append(Violation("missing_contract", "missing `## Contract`"))
        return FileResult(
            path=display,
            ok=False,
            max_preamble_lines=max_preamble_lines,
            preamble_nonempty_lines=None,
            contract_line=None,
            violations=violations,
            has_setup=has_setup,
        )

    # First H2 must be Contract.
    first_h2_idx: int | None = None
    for i in range(h1_idx + 1, len(raw)):
        if is_h2(raw[i]):
            first_h2_idx = i
            break
    if first_h2_idx is not None and first_h2_idx != contract_idx:
        violations.append(
            Violation(
                "contract_not_first_h2",
                f"`## Contract` is not the first H2 (first H2: {raw[first_h2_idx].strip()!r})",
            )
        )

    preamble_lines = raw[h1_idx + 1 : contract_idx]
    preamble_nonempty = [line for line in preamble_lines if line.strip()]
    preamble_nonempty_count = len(preamble_nonempty)
    if preamble_nonempty_count > max_preamble_lines:
        violations.append(
            Violation(
                "preamble_too_long",
                f"preamble has {preamble_nonempty_count} non-empty lines (max {max_preamble_lines})",
            )
        )

    # No headings allowed before Contract other than the first H1 itself.
    for line in preamble_lines:
        if is_heading(line):
            violations.append(
                Violation(
                    "heading_before_contract",
                    "found a markdown heading before `## Contract` (move it after the Contract)",
                )
            )
            break

    return FileResult(
        path=display,
        ok=not violations,
        max_preamble_lines=max_preamble_lines,
        preamble_nonempty_lines=preamble_nonempty_count,
        contract_line=contract_idx + 1,
        violations=violations,
        has_setup=has_setup,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SKILL.md structure for format compliance.")
    parser.add_argument(
        "--format",
        choices=["summary", "json"],
        default="summary",
        help="Output format (default: summary).",
    )
    parser.add_argument(
        "--max-preamble-lines",
        type=int,
        default=MAX_PREAMBLE_DEFAULT,
        help=f"Maximum allowed non-empty preamble lines between H1 and Contract (default: {MAX_PREAMBLE_DEFAULT}).",
    )
    args = parser.parse_args()

    if args.max_preamble_lines < 0:
        eprint("error: --max-preamble-lines must be >= 0")
        return 2

    root = repo_root()
    files = tracked_skill_mds(root)
    results = [audit_file(p, root, args.max_preamble_lines) for p in files]

    violations = [r for r in results if not r.ok]
    stats: dict[str, int] = {}
    for r in violations:
        for v in r.violations:
            stats[v.kind] = stats.get(v.kind, 0) + 1

    if args.format == "json":
        payload = {
            "repo_root": root.as_posix(),
            "max_preamble_lines": args.max_preamble_lines,
            "files_checked": len(results),
            "files_with_violations": len(violations),
            "violation_counts": dict(sorted(stats.items())),
            "files": [
                {
                    "path": r.path,
                    "ok": r.ok,
                    "preamble_nonempty_lines": r.preamble_nonempty_lines,
                    "contract_line": r.contract_line,
                    "has_setup": r.has_setup,
                    "violations": [{"kind": v.kind, "message": v.message} for v in r.violations],
                }
                for r in results
            ],
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
        return 1 if violations else 0

    # summary
    eprint(f"skills/audit_skill_md_format: checked {len(results)} SKILL.md files")
    if not violations:
        eprint("skills/audit_skill_md_format: ok (no violations)")
        return 0

    eprint(f"skills/audit_skill_md_format: violations in {len(violations)} file(s)")
    for kind, count in sorted(stats.items()):
        eprint(f"- {kind}: {count}")
    eprint("")
    for r in violations:
        pre = r.preamble_nonempty_lines if r.preamble_nonempty_lines is not None else "?"
        line = r.contract_line if r.contract_line is not None else "?"
        eprint(f"{r.path}: contract_line={line}, preamble_nonempty_lines={pre}")
        for v in r.violations:
            eprint(f"  - {v.kind}: {v.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
