#!/usr/bin/env python3
"""Validate an active agent-scope-lock around Codex writes."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from hook_common import ALLOW, emit_block, read_payload, tool_input_dict

VALIDATE_COMMAND = ("validate", "--changes", "all", "--format", "json")
TIMEOUT_SECONDS = 8
MAX_PATHS = 6


def emit_system_message(message: str) -> None:
    sys.stdout.write(json.dumps({"systemMessage": message}))
    sys.stdout.write("\n")


def hook_event(payload: dict[str, Any]) -> str:
    for key in ("hook_event_name", "hookEventName"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def cwd_from_payload(payload: dict[str, Any]) -> Path:
    tool_input = tool_input_dict(payload)
    for value in (tool_input.get("workdir"), tool_input.get("cwd"), payload.get("cwd")):
        if isinstance(value, str) and value:
            path = Path(value).expanduser()
            return path if path.is_absolute() else (Path.cwd() / path).resolve()
    return Path.cwd()


def parse_json(text: str) -> dict[str, Any]:
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def error_code(data: dict[str, Any]) -> str:
    error = data.get("error")
    if not isinstance(error, dict):
        return ""
    code = error.get("code")
    return code if isinstance(code, str) else ""


def details_from(data: dict[str, Any]) -> dict[str, Any]:
    result = data.get("result")
    if isinstance(result, dict):
        return result
    error = data.get("error")
    if isinstance(error, dict):
        details = error.get("details")
        if isinstance(details, dict):
            return details
    return {}


def path_values(values: Any) -> list[str]:
    paths: list[str] = []
    if not isinstance(values, list):
        return paths
    for value in values:
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, dict) and isinstance(value.get("path"), str):
            paths.append(value["path"])
    return paths


def format_paths(paths: list[str]) -> str:
    if not paths:
        return "unknown"
    shown = paths[:MAX_PATHS]
    suffix = "" if len(paths) <= MAX_PATHS else f", +{len(paths) - MAX_PATHS} more"
    return ", ".join(shown) + suffix


def active_lock_file(cwd: Path) -> Path | None:
    git = shutil.which("git")
    if git is None:
        return None
    try:
        completed = subprocess.run(
            [git, "rev-parse", "--git-path", "agent-scope-lock.json"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    raw_path = completed.stdout.strip()
    if not raw_path:
        return None
    lock_path = Path(raw_path)
    if not lock_path.is_absolute():
        lock_path = cwd / lock_path
    return lock_path if lock_path.is_file() else None


def validation_failure_message(data: dict[str, Any], fallback: str) -> str:
    details = details_from(data)
    violations = path_values(details.get("violations"))
    allowed_paths = path_values(details.get("allowed_paths"))

    if violations:
        return (
            "agent-scope-lock blocked out-of-scope changes: "
            f"{format_paths(violations)}. Allowed scope: {format_paths(allowed_paths)}. "
            "Run `agent-scope-lock validate --changes all --format json` for details."
        )

    error = data.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        fallback = error["message"]
    return (
        "agent-scope-lock could not validate the active lock: "
        f"{fallback}. Run `agent-scope-lock validate --changes all --format json` for details."
    )


def emit_guard_message(payload: dict[str, Any], message: str) -> None:
    if hook_event(payload) == "Stop":
        emit_system_message(message)
        return
    emit_block(message)


def main() -> int:
    payload = read_payload()
    cwd = cwd_from_payload(payload)
    binary = shutil.which("agent-scope-lock")

    if binary is None:
        if active_lock_file(cwd) is not None:
            emit_guard_message(
                payload,
                "agent-scope-lock is active but the `agent-scope-lock` binary is not on PATH; "
                "install nils-cli or clear the lock before continuing.",
            )
        return ALLOW

    try:
        completed = subprocess.run(
            [binary, *VALIDATE_COMMAND],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        if active_lock_file(cwd) is not None:
            emit_guard_message(payload, "agent-scope-lock validation timed out for the active lock.")
        return ALLOW
    except OSError as exc:
        if active_lock_file(cwd) is not None:
            emit_guard_message(payload, f"agent-scope-lock validation failed for the active lock: {exc}.")
        return ALLOW

    data = parse_json(completed.stdout)
    if completed.returncode == 0:
        return ALLOW
    if error_code(data) == "missing-lock":
        return ALLOW
    if error_code(data) == "git-command-failed" and active_lock_file(cwd) is None:
        return ALLOW

    if active_lock_file(cwd) is not None or error_code(data) == "scope-violations":
        fallback = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        emit_guard_message(payload, validation_failure_message(data, fallback))
    return ALLOW


if __name__ == "__main__":
    sys.exit(main())
