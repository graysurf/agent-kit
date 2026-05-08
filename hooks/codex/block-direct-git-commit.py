#!/usr/bin/env python3
"""PreToolUse hook: block direct git commit invocations.

Agents should use semantic-commit or semantic-commit-autostage so commit
messages, validation, and dirty-tree handling stay auditable.
"""

from __future__ import annotations

import re
import sys

from hook_common import ALLOW, command_from, emit_block, read_payload

BLOCK_REASON = (
    "Do not use git commit directly. Use semantic-commit or "
    "semantic-commit-autostage instead."
)

GIT_COMMIT_RE = re.compile(
    r"""(?:^|[\s;&|()])
        git
        (?:\s+-[cC]\s+\S+)*
        \s+commit
        (?:\s|$|[;&|)])
    """,
    re.VERBOSE,
)


def main() -> int:
    command = command_from(read_payload())
    if command and GIT_COMMIT_RE.search(command):
        emit_block(BLOCK_REASON)
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
