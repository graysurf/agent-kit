#!/usr/bin/env python3
"""Scan `.mcp.json` changes for secrets and absolute home paths."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from hook_common import ALLOW, emit_block, patch_text_candidates, read_payload, tool_input_dict

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-(?!ant-)[A-Za-z0-9_-]{16,}\b")),
    ("GitHub PAT", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("GitLab PAT", re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}\b")),
    ("Slack bot token", re.compile(r"\bxoxb-[A-Za-z0-9-]{10,}\b")),
    ("Slack user token", re.compile(r"\bxoxp-[A-Za-z0-9-]{10,}\b")),
    ("xAI key", re.compile(r"\bxai-[A-Za-z0-9_-]{16,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9\-_.=]{8,}")),
    ("macOS home path", re.compile(r"/Users/[^/\s\"']+/")),
    ("Linux home path", re.compile(r"/home/[^/\s\"']+/")),
)

BLOCK_TEMPLATE = (
    ".mcp.json change blocked: detected secret or absolute-path pattern(s):\n"
    "{hits}\n\n"
    "rule: AGENTS.md requires .mcp.json to avoid secrets and machine-local "
    "absolute paths.\n"
    "fix: move machine-local values to ignored local config for the active "
    "tool.\n"
    "escape hatch: set SKIP_MCP_SCAN=1 only after verifying a false positive."
)


def scan(content: str) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, pattern in PATTERNS:
        if name in seen:
            continue
        match = pattern.search(content)
        if match:
            seen.add(name)
            hits.append((name, match.group(0)))
    return hits


def masked_sample(sample: str) -> str:
    if sample.startswith("/Users/") or sample.startswith("/home/"):
        return "<absolute home path>"
    if len(sample) <= 8:
        return "<redacted>"
    return f"{sample[:4]}...{sample[-4:]}"


def format_hits(hits: list[tuple[str, str]]) -> str:
    return "\n".join(f"  - {name}: {masked_sample(sample)}" for name, sample in hits)


def is_mcp_json(file_path: str) -> bool:
    return os.path.basename(file_path) == ".mcp.json"


def proposed_content(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "Write":
        return str(tool_input.get("content", ""))
    if tool_name == "Edit":
        return str(tool_input.get("new_string", ""))
    if tool_name == "NotebookEdit":
        return str(tool_input.get("new_source", ""))
    return ""


def added_mcp_lines_from_apply_patch(patch_text: str) -> list[str]:
    lines: list[str] = []
    current_is_mcp = False
    for line in patch_text.splitlines():
        if line.startswith("*** Add File: "):
            current_is_mcp = is_mcp_json(line.removeprefix("*** Add File: ").strip())
            continue
        if line.startswith("*** Update File: "):
            current_is_mcp = is_mcp_json(line.removeprefix("*** Update File: ").strip())
            continue
        if line.startswith("*** Delete File: "):
            current_is_mcp = False
            continue
        if line.startswith("*** Move to: "):
            current_is_mcp = is_mcp_json(line.removeprefix("*** Move to: ").strip())
            continue
        if current_is_mcp and line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
    return lines


def hook_contents_to_scan(payload: dict[str, Any]) -> list[str]:
    contents: list[str] = []
    tool_name = str(payload.get("tool_name", ""))
    tool_input = tool_input_dict(payload)

    file_path = str(tool_input.get("file_path", ""))
    if is_mcp_json(file_path):
        content = proposed_content(tool_name, tool_input)
        if content:
            contents.append(content)

    for candidate in patch_text_candidates(payload):
        added_lines = added_mcp_lines_from_apply_patch(candidate)
        if added_lines:
            contents.append("\n".join(added_lines))

    return contents


def run_hook_mode() -> int:
    payload = read_payload()
    hits: list[tuple[str, str]] = []
    for content in hook_contents_to_scan(payload):
        hits.extend(scan(content))
    if hits:
        reason = BLOCK_TEMPLATE.format(hits=format_hits(hits))
        emit_block(reason)
    return ALLOW


def staged_mcp_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        print(f"error: git diff failed: {stderr}", file=sys.stderr)
        return []
    names = [name for name in result.stdout.decode(errors="replace").split("\0") if name]
    return [name for name in names if is_mcp_json(name)]


def staged_content(file_path: str) -> str | None:
    result = subprocess.run(["git", "show", f":{file_path}"], capture_output=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        print(f"error: cannot read staged {file_path}: {stderr}", file=sys.stderr)
        return None
    return result.stdout.decode(errors="replace")


def run_staged_mode() -> int:
    files = staged_mcp_files()
    if not files:
        print("mcp-scan: no staged .mcp.json files")
        return 0

    exit_code = 0
    for file_path in files:
        content = staged_content(file_path)
        if content is None:
            exit_code = 2
            continue
        hits = scan(content)
        if hits:
            print(f"mcp-scan: secrets / absolute paths in staged {file_path}:")
            print(format_hits(hits))
            exit_code = 1
    if exit_code == 0:
        print(f"mcp-scan: scanned {len(files)} staged .mcp.json file(s), clean")
    return exit_code


def run_paths_mode(paths: list[str]) -> int:
    exit_code = 0
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            print(f"error: not a file: {raw_path}", file=sys.stderr)
            exit_code = 2
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"error: cannot read {raw_path}: {exc}", file=sys.stderr)
            exit_code = 2
            continue
        hits = scan(content)
        if hits:
            print(f"mcp-scan: secrets / absolute paths in {raw_path}:")
            print(format_hits(hits))
            exit_code = 1
    if exit_code == 0:
        print(f"mcp-scan: scanned {len(paths)} file(s), clean")
    return exit_code


def main() -> int:
    if os.environ.get("SKIP_MCP_SCAN") == "1":
        if len(sys.argv) > 1:
            print("[skipped:mcp-scan]", file=sys.stderr)
        return 0

    if len(sys.argv) == 1:
        return run_hook_mode()

    parser = argparse.ArgumentParser(
        description="Scan .mcp.json for secrets and absolute home paths.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--staged", action="store_true", help="Scan staged .mcp.json files.")
    group.add_argument("--paths", nargs="+", metavar="FILE", help="Scan specific paths.")
    args = parser.parse_args()

    if args.staged:
        return run_staged_mode()
    paths: list[str] = args.paths
    return run_paths_mode(paths)


if __name__ == "__main__":
    sys.exit(main())
