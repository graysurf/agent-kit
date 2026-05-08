#!/usr/bin/env python3
"""PreToolUse hook: block direct GitHub PR and GitLab MR creation."""

from __future__ import annotations

import re
import sys

from hook_common import ALLOW, command_from, emit_block, read_payload

ALLOWED_PR_SKILLS: frozenset[str] = frozenset(
    {
        "create-feature-pr",
        "create-bug-pr",
        "create-plan-issue-sprint-pr",
    }
)
ALLOWED_MR_SKILLS: frozenset[str] = frozenset()

BLOCK_REASON_PR = (
    "Do not run gh pr create directly. Open PRs through an agent-kit PR "
    "workflow so the body follows the standard template and the call is "
    "auditable. Skill bypass: prefix the command with "
    "AGENT_KIT_PR_SKILL=<exact allowed skill name>."
)

BLOCK_REASON_MR = (
    "Do not run glab mr create directly. Add or use an audited agent-kit MR "
    "workflow before opening MRs directly. Skill bypass requires "
    "AGENT_KIT_PR_SKILL=<exact allowed MR skill name> after this hook is "
    "updated to allow that skill."
)

GH_PR_CREATE_RE = re.compile(
    r"""(?:^|[\s;&|()])
        gh
        (?:\s+(?:-R|--repo)\s+\S+)*
        \s+pr\s+create
        (?:\s|$|[;&|)])
    """,
    re.VERBOSE,
)

GLAB_MR_CREATE_RE = re.compile(
    r"""(?:^|[\s;&|()])
        glab
        (?:\s+(?:-R|--repo)\s+\S+)*
        \s+mr\s+create
        (?:\s|$|[;&|)])
    """,
    re.VERBOSE,
)

SKILL_MARKER_RE = re.compile(
    r"(?:^|[\s;&|()])AGENT_KIT_PR_SKILL=(?P<value>\S+)"
)


def marker_value(command: str) -> str | None:
    match = SKILL_MARKER_RE.search(command)
    return match.group("value") if match else None


def main() -> int:
    command = command_from(read_payload())
    if not command:
        return ALLOW

    marker = marker_value(command)
    if GH_PR_CREATE_RE.search(command) and marker not in ALLOWED_PR_SKILLS:
        emit_block(BLOCK_REASON_PR)
        return ALLOW
    if GLAB_MR_CREATE_RE.search(command) and marker not in ALLOWED_MR_SKILLS:
        emit_block(BLOCK_REASON_MR)
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
