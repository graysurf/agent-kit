#!/usr/bin/env python3
"""PreToolUse hook: block direct Python invocations in managed Python repos."""

from __future__ import annotations

import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from hook_common import ALLOW, command_from, emit_block, read_payload

BYPASS_ENV = "AGENT_KIT_ALLOW_SYSTEM_PYTHON"

ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*")
PYTHON_NAME_RE = re.compile(r"^python(?:3(?:\.\d+)?)?$")
SEPARATOR_TOKENS = {";", "&&", "||", "|", "(", ")"}


@dataclass(frozen=True)
class PythonManager:
    kind: str
    root: Path
    marker: Path
    venv_name: str | None = None


def has_bypass(command: str) -> bool:
    if os.environ.get(BYPASS_ENV) in {"1", "true", "TRUE", "yes", "YES"}:
        return True
    return bool(
        re.search(
            rf"(?:^|[\s;&|()]){re.escape(BYPASS_ENV)}=(?:1|true|TRUE|yes|YES)(?:\s|$|[;&|()])",
            command,
        )
    )


def pyproject_declares_uv(path: Path) -> bool:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            header = line.split("#", 1)[0].strip()
            if header == "[tool.uv]" or header.startswith("[tool.uv."):
                return True
    except OSError:
        return False
    return False


def find_python_manager(start: Path) -> PythonManager | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        uv_lock = directory / "uv.lock"
        if uv_lock.exists():
            return PythonManager("uv", directory, uv_lock)

        pyproject = directory / "pyproject.toml"
        if pyproject.exists() and pyproject_declares_uv(pyproject):
            return PythonManager("uv", directory, pyproject)

        for venv_name in (".venv", "venv"):
            pyvenv_cfg = directory / venv_name / "pyvenv.cfg"
            if pyvenv_cfg.exists():
                return PythonManager("venv", directory, pyvenv_cfg, venv_name)

    return None


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


def is_project_venv_python(token: str) -> bool:
    if "/" not in token:
        return False
    parts = PurePosixPath(token).parts
    return len(parts) >= 3 and parts[-2] == "bin" and parts[-3] in {".venv", "venv"}


def is_direct_python_token(token: str) -> bool:
    if is_project_venv_python(token):
        return False
    if not PYTHON_NAME_RE.match(basename(token)):
        return False
    return "/" not in token or token.startswith("/")


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


def command_python_token(simple_command: list[str]) -> str | None:
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
    return simple_command[index] if is_direct_python_token(simple_command[index]) else None


def direct_python_token(command: str) -> str | None:
    simple_command: list[str] = []
    for token in shell_tokens(command):
        if is_separator(token):
            found = command_python_token(simple_command)
            if found:
                return found
            simple_command = []
            continue
        simple_command.append(token)
    return command_python_token(simple_command)


def block_reason(executable: str, manager: PythonManager) -> str:
    if manager.kind == "uv":
        fix = "Use `uv run --locked python ...` from this workspace."
        manager_label = "uv"
    else:
        venv_name = manager.venv_name or ".venv"
        fix = f"Use `{venv_name}/bin/python ...` from this workspace."
        manager_label = "a local virtualenv"

    return (
        f"Do not run `{executable}` directly here. This workspace appears to use {manager_label} "
        f"({manager.marker}).\n"
        f"  fix: {fix}\n"
        f"  escape hatch: prefix the command with `{BYPASS_ENV}=1` when system Python is intentional."
    )


def main() -> int:
    payload = read_payload()
    command = command_from(payload)
    if not command or has_bypass(command):
        return ALLOW

    executable = direct_python_token(command)
    if not executable:
        return ALLOW

    manager = find_python_manager(Path.cwd())
    if manager is not None:
        emit_block(block_reason(executable, manager))
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
