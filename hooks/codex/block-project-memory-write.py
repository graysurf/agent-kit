#!/usr/bin/env python3
"""PreToolUse hook: block project-state memory writes."""

from __future__ import annotations

import re
import sys

from hook_common import ALLOW, emit_block, file_paths_from_payload, read_payload

BLOCK_REASON = (
    "Blocked project-state memory write. Do not store project state in "
    "personal memory; use repository docs, git history, or agent-docs "
    "runbooks instead."
)

PROJECT_MEMORY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:^|/)\.claude/projects/[^/]+/memory/project_[^/]*\.md$"),
    re.compile(r"(?:^|/)\.config/agent-memory/(?:[^/]+/)*project_[^/]*\.md$"),
    re.compile(r"(?:^|/)\.codex/memories/(?:[^/]+/)*project_[^/]*\.md$"),
)


def is_project_memory_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(pattern.search(normalized) for pattern in PROJECT_MEMORY_PATTERNS)


def main() -> int:
    payload = read_payload()
    if any(is_project_memory_path(path) for path in file_paths_from_payload(payload)):
        emit_block(BLOCK_REASON)
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
