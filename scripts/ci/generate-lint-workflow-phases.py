#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any


BEGIN_MARKER = "# BEGIN GENERATED: check-phase-map {job}"
END_MARKER = "# END GENERATED: check-phase-map {job}"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate scripts/check.sh phase steps in .github/workflows/lint.yml from scripts/lib/check/ci_phase_map.json."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Verify lint workflow generated blocks are up to date (default).")
    mode.add_argument("--write", action="store_true", help="Rewrite lint workflow generated blocks in place.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text("utf-8"))
    except FileNotFoundError:
        raise RuntimeError(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid json in {path}: {exc}") from None

    if not isinstance(data, dict):
        raise RuntimeError(f"expected json object in {path}")
    return data


def load_known_modes(path: Path) -> set[str]:
    text = path.read_text("utf-8")
    m = re.search(r"(?ms)^CHECK_MODES=\((?P<body>.*?)\)", text)
    if not m:
        raise RuntimeError(f"failed to parse CHECK_MODES from {path}")
    body = m.group("body")
    tokens = shlex.split(body, comments=True, posix=True)
    return set(tokens)


def load_phase_map(path: Path, known_modes: set[str]) -> dict[str, list[dict[str, str]]]:
    data = load_json(path)

    out: dict[str, list[dict[str, str]]] = {}
    for job, steps in data.items():
        if not isinstance(job, str):
            raise RuntimeError("ci_phase_map keys must be strings")
        if not isinstance(steps, list):
            raise RuntimeError(f"ci_phase_map['{job}'] must be a list")
        validated_steps: list[dict[str, str]] = []
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                raise RuntimeError(f"ci_phase_map['{job}'][{idx}] must be an object")
            name = step.get("name")
            mode = step.get("mode")
            pytest_args = step.get("pytest_args")

            if not isinstance(name, str) or not name.strip():
                raise RuntimeError(f"ci_phase_map['{job}'][{idx}].name must be a non-empty string")
            if not isinstance(mode, str) or not mode.strip():
                raise RuntimeError(f"ci_phase_map['{job}'][{idx}].mode must be a non-empty string")
            if mode not in known_modes:
                raise RuntimeError(f"ci_phase_map['{job}'][{idx}].mode is unknown: {mode}")
            if pytest_args is not None and not isinstance(pytest_args, str):
                raise RuntimeError(f"ci_phase_map['{job}'][{idx}].pytest_args must be a string when provided")

            row: dict[str, str] = {"name": name.strip(), "mode": mode.strip()}
            if isinstance(pytest_args, str) and pytest_args.strip():
                row["pytest_args"] = pytest_args.strip()
            validated_steps.append(row)
        out[job] = validated_steps

    return out


def render_step(indent: str, step: dict[str, str]) -> list[str]:
    cmd = f"$AGENT_HOME/scripts/check.sh --{step['mode']}"
    pytest_args = step.get("pytest_args")
    if pytest_args:
        cmd += f" -- {pytest_args}"

    return [
        f"{indent}- name: {step['name']}",
        f"{indent}  run: |",
        f"{indent}    {cmd}",
    ]


def render_block(indent: str, job: str, steps: list[dict[str, str]]) -> str:
    lines: list[str] = [f"{indent}{BEGIN_MARKER.format(job=job)}"]
    for step in steps:
        lines.extend(render_step(indent, step))
    lines.append(f"{indent}{END_MARKER.format(job=job)}")
    return "\n".join(lines) + "\n"


def replace_generated_block(workflow: str, job: str, steps: list[dict[str, str]]) -> str:
    begin = re.escape(BEGIN_MARKER.format(job=job))
    end = re.escape(END_MARKER.format(job=job))
    pattern = re.compile(
        rf"(?ms)^(?P<indent>[ \t]*){begin}\n.*?^(?P=indent){end}\n?"
    )

    match = pattern.search(workflow)
    if not match:
        raise RuntimeError(
            f"missing generated block markers for '{job}' in .github/workflows/lint.yml:\n"
            f"- {BEGIN_MARKER.format(job=job)}\n- {END_MARKER.format(job=job)}"
        )

    indent = match.group("indent")
    rendered = render_block(indent, job, steps)
    return workflow[: match.start()] + rendered + workflow[match.end() :]


def build_expected_workflow(current: str, phase_map: dict[str, list[dict[str, str]]]) -> str:
    expected = current
    for job, steps in phase_map.items():
        expected = replace_generated_block(expected, job, steps)
    return expected


def print_diff(current: str, expected: str, path: Path) -> None:
    diff = difflib.unified_diff(
        current.splitlines(keepends=True),
        expected.splitlines(keepends=True),
        fromfile=str(path),
        tofile=f"{path} (expected)",
    )
    sys.stderr.writelines(diff)


def main() -> int:
    args = parse_args()
    check_mode = True
    if args.write:
        check_mode = False
    elif args.check:
        check_mode = True

    root = repo_root()
    workflow_path = root / ".github" / "workflows" / "lint.yml"
    phase_map_path = root / "scripts" / "lib" / "check" / "ci_phase_map.json"
    check_modes_path = root / "scripts" / "lib" / "check" / "modes.sh"

    try:
        known_modes = load_known_modes(check_modes_path)
        phase_map = load_phase_map(phase_map_path, known_modes)
        current = workflow_path.read_text("utf-8")
        expected = build_expected_workflow(current, phase_map)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"error: missing file: {workflow_path}", file=sys.stderr)
        return 2

    if check_mode:
        if current != expected:
            print("error: generated lint workflow phase mapping is stale", file=sys.stderr)
            print_diff(current, expected, workflow_path)
            print("hint: run scripts/ci/generate-lint-workflow-phases.py --write", file=sys.stderr)
            return 1
        print("PASS [lint-phase-map] generated lint workflow phase mapping is up to date")
        return 0

    workflow_path.write_text(expected, "utf-8")
    print("PASS [lint-phase-map] updated .github/workflows/lint.yml generated phase mapping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

