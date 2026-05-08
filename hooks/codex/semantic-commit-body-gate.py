#!/usr/bin/env python3
"""PreToolUse hook: require a body on non-trivial semantic-commit commits."""

from __future__ import annotations

import re
import sys

from hook_common import ALLOW, command_from, emit_block, read_payload

BLOCK_REASON_TEMPLATE = (
    "semantic-commit message is missing a body\n"
    "  subject: {subject}\n"
    "  rule: non-trivial commits need 1-2 bullets explaining why and scope\n"
    "  fix: append `\\n\\n- <reason>` to --message, preferably with a HEREDOC\n"
    "  ref: $AGENT_HOME/skills/tools/devex/semantic-commit/SKILL.md\n"
    "  escape hatch: add `[no-body]` in the subject if this is truly trivial"
)

TRIVIAL_TYPES = {"chore", "docs", "style", "build"}
TRIVIAL_KEYWORDS = ("bump", "refresh", "regenerate", "pin", "lockfile")


def is_semantic_commit_commit(command: str) -> bool:
    if not re.search(r"\bsemantic-commit\s+commit\b", command):
        return False
    if re.search(r"(--validate-only|--dry-run|-h\b|--help\b)", command):
        return False
    return not re.search(
        r"\bsemantic-commit\s+(staged-context|config|help|--help)\b",
        command,
    )


def extract_message(command: str) -> str | None:
    heredoc_re = re.compile(
        r"""(?:--message|-m)
            \s+
            ["']?
            \$\(
            \s*cat\s*<<(?P<dash>-)?
            \s*
            (?P<q>['"])?
            (?P<tag>\w+)
            (?P=q)?
            \s*\n
            (?P<body>.*?)
            \n
            (?P<leading>[ \t]*)
            (?P=tag)
            \s*
            \n?
            \s*\)
            ["']?""",
        re.DOTALL | re.VERBOSE,
    )
    match = heredoc_re.search(command)
    if match:
        return match.group("body")

    double_quoted_re = re.compile(r'(?:--message|-m)\s+"((?:\\.|[^"\\])*)"', re.DOTALL)
    match = double_quoted_re.search(command)
    if match:
        raw = match.group(1)
        return (
            raw.replace("\\\\", "\x00")
            .replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\x00", "\\")
        )

    single_quoted_re = re.compile(r"(?:--message|-m)\s+'([^']*)'", re.DOTALL)
    match = single_quoted_re.search(command)
    if match:
        return match.group(1)

    return None


def split_subject_body(message: str) -> tuple[str, list[str]]:
    lines = message.splitlines()
    if not lines:
        return "", []
    subject = lines[0].rstrip()
    rest = lines[1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    body_nonempty = [line for line in rest if line.strip()]
    return subject, body_nonempty


def is_trivial_subject(subject: str) -> bool:
    stripped = subject.strip()
    if not stripped:
        return False
    lower = stripped.lower()

    if "[no-body]" in lower:
        return True

    header_match = re.match(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?:", stripped)
    if header_match:
        commit_type = header_match.group("type")
        scope = (header_match.group("scope") or "").lower()
        if commit_type in TRIVIAL_TYPES:
            return True
        scope_tokens = re.split(r"[\s,/]+", scope)
        if any(token in ("ci", "deps") for token in scope_tokens):
            return True

    subject_words = re.findall(r"[a-z]+", lower)
    return any(keyword in subject_words for keyword in TRIVIAL_KEYWORDS)


def main() -> int:
    command = command_from(read_payload())
    if not command or not is_semantic_commit_commit(command):
        return ALLOW

    message = extract_message(command)
    if message is None:
        return ALLOW

    subject, body_lines = split_subject_body(message)
    if not body_lines and not is_trivial_subject(subject):
        emit_block(BLOCK_REASON_TEMPLATE.format(subject=subject or "<unparsed>"))
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
