#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


MAX_PREAMBLE_DEFAULT = 2
FRONT_MATTER_REQUIRED_KEYS = ("name", "description")
FRONT_MATTER_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")


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


def _looks_like_front_matter_key(line: str) -> bool:
    return FRONT_MATTER_KEY_RE.match(line) is not None


def _is_quoted_scalar(value: str) -> bool:
    return value.startswith(('"', "'"))


def _quote_is_closed(lines: list[str], quote: str) -> bool:
    for line in reversed(lines):
        stripped = line.strip()
        if stripped:
            return len(stripped) > 1 and stripped.endswith(quote)
    return False


def _validate_scalar_value(value: str, line_no: int, violations: list[Violation]) -> None:
    if not value:
        violations.append(Violation("frontmatter_empty_value", f"empty front matter value at line {line_no}"))
        return
    if _is_quoted_scalar(value):
        quote = value[0]
        if not _quote_is_closed([value], quote):
            violations.append(Violation("frontmatter_unclosed_quote", f"unclosed quoted front matter value at line {line_no}"))
        return
    if value.startswith(("|", ">")):
        return
    if ": " in value:
        violations.append(
            Violation(
                "frontmatter_plain_scalar_colon",
                f"plain front matter scalar contains ': ' at line {line_no}; quote the value",
            )
        )


def _validate_multiline_scalar(lines: list[tuple[int, str]], violations: list[Violation]) -> None:
    nonempty = [(line_no, line.strip()) for line_no, line in lines if line.strip()]
    if not nonempty:
        first_line = lines[0][0] if lines else "?"
        violations.append(Violation("frontmatter_empty_value", f"empty front matter value at line {first_line}"))
        return

    first_line_no, first_value = nonempty[0]
    if _is_quoted_scalar(first_value):
        quote = first_value[0]
        if not _quote_is_closed([value for _, value in nonempty], quote):
            violations.append(
                Violation("frontmatter_unclosed_quote", f"unclosed quoted front matter value at line {first_line_no}")
            )
        return
    if first_value.startswith(("|", ">")):
        return

    for line_no, value in nonempty:
        if ": " in value:
            violations.append(
                Violation(
                    "frontmatter_plain_scalar_colon",
                    f"plain front matter scalar contains ': ' at line {line_no}; quote the multiline value",
                )
            )
            return


def validate_front_matter(raw: list[str]) -> list[Violation]:
    violations: list[Violation] = []
    if not raw or raw[0].strip() != "---":
        return [Violation("frontmatter_missing_start", "missing YAML front matter start marker (`---`)")]

    end_idx: int | None = None
    for i in range(1, len(raw)):
        if raw[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return [Violation("frontmatter_missing_end", "missing YAML front matter end marker (`---`)")]

    seen_keys: set[str] = set()
    lines = raw[1:end_idx]
    i = 0
    while i < len(lines):
        line = lines[i]
        line_no = i + 2
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if line[:1].isspace():
            violations.append(
                Violation("frontmatter_unexpected_continuation", f"unexpected front matter continuation at line {line_no}")
            )
            i += 1
            continue

        match = FRONT_MATTER_KEY_RE.match(line)
        if match is None:
            violations.append(Violation("frontmatter_invalid_line", f"invalid front matter line at line {line_no}"))
            i += 1
            continue

        key, value = match.group(1), (match.group(2) or "")
        if key in seen_keys:
            violations.append(Violation("frontmatter_duplicate_key", f"duplicate front matter key `{key}` at line {line_no}"))
        seen_keys.add(key)

        if value:
            _validate_scalar_value(value, line_no, violations)
            i += 1
            continue

        block: list[tuple[int, str]] = []
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            if next_line.strip() and not next_line[:1].isspace() and _looks_like_front_matter_key(next_line):
                break
            block.append((j + 2, next_line))
            j += 1
        _validate_multiline_scalar(block, violations)
        i = j

    for key in FRONT_MATTER_REQUIRED_KEYS:
        if key not in seen_keys:
            violations.append(Violation("frontmatter_missing_required_key", f"missing front matter key `{key}`"))

    return violations


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

    violations: list[Violation] = validate_front_matter(raw)

    h1_idx: int | None = None
    for i, line in enumerate(raw):
        if is_h1(line):
            h1_idx = i
            break

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
