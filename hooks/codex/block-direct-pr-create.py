#!/usr/bin/env python3
"""PreToolUse hook: block direct GitHub PR and GitLab MR creation."""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import PurePosixPath

from hook_common import ALLOW, command_from, emit_block, read_payload

ALLOWED_PR_SKILLS: frozenset[str] = frozenset(
    {
        "create-github-pr",
        "create-plan-issue-sprint-pr",
    }
)
ALLOWED_MR_SKILLS: frozenset[str] = frozenset(
    {
        "create-gitlab-mr",
    }
)

BLOCK_REASON_PR = (
    "Do not run gh pr create directly. Open PRs through an agent-kit PR "
    "workflow so the body follows the standard template and the call is "
    "auditable. Skill bypass: prefix the command with "
    "AGENT_KIT_PR_SKILL=<exact allowed skill name>."
)

BLOCK_REASON_MR = (
    "Do not create GitLab MRs directly. Use the audited agent-kit MR workflow "
    "`create-gitlab-mr` so the body, branch handling, and source-branch policy "
    "are reviewable. Skill bypass: prefix the command with "
    "AGENT_KIT_PR_SKILL=<exact allowed MR skill name>."
)

SKILL_MARKER_RE = re.compile(
    r"(?:^|[\s;&|()])AGENT_KIT_PR_SKILL=(?P<value>\S+)"
)
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*")
SEPARATOR_TOKENS = {";", "&&", "||", "|", "(", ")"}
CLI_OPTIONS_WITH_VALUE = {"-R", "--repo"}
CLI_OPTIONS_WITH_VALUE_PREFIXES = ("--repo=",)
GLAB_API_METHOD_FLAGS = {"-X", "--method"}
GLAB_API_POST_PARAMETER_FLAGS = {"-F", "--field", "-f", "--raw-field", "--form"}
MR_ENDPOINT_RE = re.compile(r"(?:^|/)merge_requests(?:$|[/?#])")


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


def cli_command_index(simple_command: list[str], command_name: str) -> int | None:
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
    return index if basename(simple_command[index]) == command_name else None


def skip_cli_global_options(tokens: list[str], index: int) -> int:
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            return index + 1
        if token in CLI_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if any(token.startswith(prefix) for prefix in CLI_OPTIONS_WITH_VALUE_PREFIXES):
            index += 1
            continue
        if token.startswith("-R") and token != "-R":
            index += 1
            continue
        if token.startswith("-") and token != "-":
            index += 1
            continue
        return index
    return index


def cli_subcommands(simple_command: list[str], command_name: str) -> list[str]:
    command_index = cli_command_index(simple_command, command_name)
    if command_index is None:
        return []

    index = skip_cli_global_options(simple_command, command_index + 1)
    return simple_command[index:]


def invokes_gh_pr_create(simple_command: list[str]) -> bool:
    args = cli_subcommands(simple_command, "gh")
    return args[:2] == ["pr", "create"]


def invokes_glab_mr_create(simple_command: list[str]) -> bool:
    args = cli_subcommands(simple_command, "glab")
    return args[:2] == ["mr", "create"]


def api_method_is_post(args: list[str]) -> bool:
    for index, token in enumerate(args):
        upper = token.upper()
        if token in GLAB_API_METHOD_FLAGS and index + 1 < len(args):
            return args[index + 1].upper() == "POST"
        if upper in {"-XPOST", "-X=POST", "--METHOD=POST"}:
            return True
        if upper.startswith("--METHOD="):
            return upper.split("=", 1)[1] == "POST"
        if token in GLAB_API_POST_PARAMETER_FLAGS:
            return True
        if any(token.startswith(f"{flag}=") for flag in GLAB_API_POST_PARAMETER_FLAGS):
            return True
    return False


def api_has_merge_requests_endpoint(args: list[str]) -> bool:
    return any(MR_ENDPOINT_RE.search(token) for token in args)


def invokes_glab_api_mr_create(simple_command: list[str]) -> bool:
    args = cli_subcommands(simple_command, "glab")
    if args[:1] != ["api"]:
        return False
    api_args = args[1:]
    return api_method_is_post(api_args) and api_has_merge_requests_endpoint(api_args)


def iter_simple_commands(command: str) -> list[list[str]]:
    simple_commands: list[list[str]] = []
    current: list[str] = []
    for token in shell_tokens(command):
        if is_separator(token):
            if current:
                simple_commands.append(current)
                current = []
            continue
        current.append(token)
    if current:
        simple_commands.append(current)
    return simple_commands


def invokes_pr_create(command: str) -> bool:
    return any(invokes_gh_pr_create(simple_command) for simple_command in iter_simple_commands(command))


def invokes_mr_create(command: str) -> bool:
    return any(
        invokes_glab_mr_create(simple_command) or invokes_glab_api_mr_create(simple_command)
        for simple_command in iter_simple_commands(command)
    )


def marker_value(command: str) -> str | None:
    match = SKILL_MARKER_RE.search(command)
    return match.group("value") if match else None


def main() -> int:
    command = command_from(read_payload())
    if not command:
        return ALLOW

    marker = marker_value(command)
    if invokes_pr_create(command) and marker not in ALLOWED_PR_SKILLS:
        emit_block(BLOCK_REASON_PR)
        return ALLOW
    if invokes_mr_create(command) and marker not in ALLOWED_MR_SKILLS:
        emit_block(BLOCK_REASON_MR)
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
