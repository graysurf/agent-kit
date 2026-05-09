#!/usr/bin/env python3
"""PreToolUse hook: block direct git commit invocations.

Agents should use semantic-commit or semantic-commit-autostage so commit
messages, validation, and dirty-tree handling stay auditable.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import PurePosixPath

from hook_common import ALLOW, command_from, emit_block, read_payload

BLOCK_REASON = (
    "Do not use git commit directly. Use semantic-commit or "
    "semantic-commit-autostage instead."
)

ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*")
SEPARATOR_TOKENS = {";", "&&", "||", "|", "(", ")"}
GIT_OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--config-env",
    "--exec-path",
    "--git-dir",
    "--namespace",
    "--work-tree",
}
GIT_OPTIONS_WITH_VALUE_PREFIXES = (
    "--config-env=",
    "--exec-path=",
    "--git-dir=",
    "--namespace=",
    "--work-tree=",
)


def shell_tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return []


def is_separator(token: str) -> bool:
    return token in SEPARATOR_TOKENS or bool(token) and all(char in ";&|()" for char in token)


def basename(token: str) -> str:
    return PurePosixPath(token).name


def is_assignment(token: str) -> bool:
    return bool(ASSIGNMENT_RE.match(token))


def skip_env_prefix(tokens: list[str], index: int) -> int:
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            return index + 1
        if is_assignment(token):
            index += 1
            continue
        if token in {"-i", "--ignore-environment", "-0", "--null"}:
            index += 1
            continue
        if token in {"-u", "--unset"}:
            index += 2
            continue
        if token.startswith("--unset="):
            index += 1
            continue
        if token.startswith("-") and token != "-":
            index += 1
            continue
        return index
    return index


def git_command_index(simple_command: list[str]) -> int | None:
    index = 0
    while index < len(simple_command) and is_assignment(simple_command[index]):
        index += 1
    if index >= len(simple_command):
        return None

    command = basename(simple_command[index])
    if command == "env":
        index = skip_env_prefix(simple_command, index + 1)
    elif command == "time":
        index += 1
        while index < len(simple_command) and simple_command[index].startswith("-"):
            index += 1
    elif command in {"command", "exec"}:
        if index + 1 < len(simple_command) and simple_command[index + 1] in {"-v", "-V"}:
            return None
        index += 1

    if index >= len(simple_command):
        return None
    return index if basename(simple_command[index]) == "git" else None


def git_subcommand(simple_command: list[str]) -> str | None:
    git_index = git_command_index(simple_command)
    if git_index is None:
        return None

    index = git_index + 1
    while index < len(simple_command):
        token = simple_command[index]
        if token == "--":
            return None
        if token in GIT_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if token.startswith("-C") and token != "-C":
            index += 1
            continue
        if token.startswith("-c") and token != "-c":
            index += 1
            continue
        if token.startswith(GIT_OPTIONS_WITH_VALUE_PREFIXES):
            index += 1
            continue
        if token.startswith("-") and token != "-":
            index += 1
            continue
        return token
    return None


def invokes_git_commit(command: str) -> bool:
    simple_command: list[str] = []
    for token in shell_tokens(command):
        if is_separator(token):
            if git_subcommand(simple_command) == "commit":
                return True
            simple_command = []
            continue
        simple_command.append(token)
    return git_subcommand(simple_command) == "commit"


def main() -> int:
    command = command_from(read_payload())
    if command and invokes_git_commit(command):
        emit_block(BLOCK_REASON)
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
