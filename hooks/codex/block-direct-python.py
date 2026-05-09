#!/usr/bin/env python3
"""PreToolUse hook: block direct Python invocations in managed Python repos."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from hook_common import ALLOW, command_from, emit_block, read_payload, tool_input_dict

BYPASS_ENV = "AGENT_KIT_ALLOW_SYSTEM_PYTHON"

ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*")
PYTHON_NAME_RE = re.compile(r"^python(?:3(?:\.\d+)?)?$")
SEPARATOR_TOKENS = {";", "&&", "||", "|", "(", ")"}
WORKDIR_KEYS = {"cwd", "current_working_directory", "workdir", "working_directory"}


@dataclass(frozen=True)
class PythonManager:
    kind: str
    root: Path
    marker: Path
    venv_name: str | None = None


@dataclass(frozen=True)
class PythonInvocation:
    executable: str
    cwd: Path


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


def cd_target(simple_command: list[str], cwd: Path) -> Path | None:
    index = 0
    while index < len(simple_command) and is_assignment(simple_command[index]):
        index += 1
    if index >= len(simple_command) or basename(simple_command[index]) != "cd":
        return None

    index += 1
    while index < len(simple_command) and simple_command[index] in {"-L", "-P", "-e"}:
        index += 1
    if index < len(simple_command) and simple_command[index] == "--":
        index += 1

    if index >= len(simple_command):
        target = Path.home()
    else:
        raw_target = simple_command[index]
        if raw_target == "-":
            return None
        target = Path(raw_target).expanduser()

    if not target.is_absolute():
        target = cwd / target
    return target


def iter_workdir_values(value: Any) -> list[str]:
    values: list[str] = []
    if not isinstance(value, Mapping):
        return values
    for key, nested in value.items():
        if key in WORKDIR_KEYS and isinstance(nested, str) and nested:
            values.append(nested)
        elif isinstance(nested, Mapping):
            values.extend(iter_workdir_values(nested))
    return values


def path_from_payload(payload: dict[str, object]) -> Path:
    tool_input = tool_input_dict(payload)
    for value in iter_workdir_values(tool_input):
        path = Path(value).expanduser()
        return path if path.is_absolute() else Path.cwd() / path
    transcript_workdir = path_from_transcript(payload)
    if transcript_workdir is not None:
        return transcript_workdir
    for value in iter_workdir_values(payload):
        path = Path(value).expanduser()
        return path if path.is_absolute() else Path.cwd() / path
    return Path.cwd()


def path_from_transcript(payload: dict[str, object]) -> Path | None:
    tool_use_id = payload.get("tool_use_id")
    transcript_path = payload.get("transcript_path")
    if not isinstance(tool_use_id, str) or not isinstance(transcript_path, str):
        return None

    path = Path(transcript_path).expanduser()
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None

    for line in reversed(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_payload = event.get("payload") if isinstance(event, Mapping) else None
        if not isinstance(event_payload, Mapping):
            continue
        if event_payload.get("call_id") != tool_use_id:
            continue
        arguments = event_payload.get("arguments")
        if not isinstance(arguments, str):
            return None
        try:
            parsed_arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return None
        for value in iter_workdir_values(parsed_arguments):
            workdir = Path(value).expanduser()
            return workdir if workdir.is_absolute() else Path.cwd() / workdir
        return None
    return None


def direct_python_invocation(command: str, start_cwd: Path) -> PythonInvocation | None:
    simple_command: list[str] = []
    current_cwd = start_cwd
    for token in shell_tokens(command):
        if is_separator(token):
            found = command_python_token(simple_command)
            if found:
                return PythonInvocation(found, current_cwd)
            if token in {";", "&&"}:
                current_cwd = cd_target(simple_command, current_cwd) or current_cwd
            simple_command = []
            continue
        simple_command.append(token)
    found = command_python_token(simple_command)
    if found:
        return PythonInvocation(found, current_cwd)
    return None


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

    invocation = direct_python_invocation(command, path_from_payload(payload))
    if not invocation:
        return ALLOW

    manager = find_python_manager(invocation.cwd)
    if manager is not None:
        emit_block(block_reason(invocation.executable, manager))
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
