from __future__ import annotations

import json
import re
import shlex
import subprocess
from pathlib import Path

import pytest

LEGACY_PHASE_COMMAND_PATTERNS = {
    "scripts/lint.sh --shell": r"(?m)^\s*\$AGENT_HOME/scripts/lint\.sh --shell\s*$",
    "scripts/lint.sh --python": r"(?m)^\s*\$AGENT_HOME/scripts/lint\.sh --python\s*$",
    "scripts/ci/markdownlint-audit.sh --strict": r"(?m)^\s*\$AGENT_HOME/scripts/ci/markdownlint-audit\.sh --strict\s*$",
    "scripts/ci/third-party-artifacts-audit.sh --strict": r"(?m)^\s*\$AGENT_HOME/scripts/ci/third-party-artifacts-audit\.sh --strict\s*$",
    "zsh -f scripts/audit-env-bools.zsh --check": r"(?m)^\s*zsh -f \$AGENT_HOME/scripts/audit-env-bools\.zsh --check\s*$",
    "validate_skill_contracts.sh": r"(?m)^\s*\$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts\.sh\s*$",
    "audit-skill-layout.sh": r"(?m)^\s*\$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/audit-skill-layout\.sh\s*$",
    "scripts/test.sh": r"(?m)^\s*\$AGENT_HOME/scripts/test\.sh\s*$",
}

CHECK_COMMAND_PATTERN = re.compile(r"scripts/check\.sh(?P<args>[^\n\r]*)")
MODE_PATTERN = re.compile(r"--[a-z0-9-]+")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (_repo_root() / path).read_text("utf-8")


def _load_ci_phase_map() -> dict[str, list[dict[str, str]]]:
    payload = json.loads(_read("scripts/lib/check/ci_phase_map.json"))
    assert isinstance(payload, dict)
    normalized: dict[str, list[dict[str, str]]] = {}
    for job, rows in payload.items():
        assert isinstance(job, str)
        assert isinstance(rows, list)
        normalized_rows: list[dict[str, str]] = []
        for row in rows:
            assert isinstance(row, dict)
            name = row.get("name")
            mode = row.get("mode")
            assert isinstance(name, str) and name.strip(), f"invalid ci phase name in {job}: {row}"
            assert isinstance(mode, str) and mode.strip(), f"invalid ci phase mode in {job}: {row}"
            out: dict[str, str] = {"name": name.strip(), "mode": mode.strip()}
            pytest_args = row.get("pytest_args")
            if pytest_args is not None:
                assert isinstance(pytest_args, str), f"pytest_args must be string in {job}: {row}"
                out["pytest_args"] = pytest_args
            normalized_rows.append(out)
        normalized[job] = normalized_rows
    return normalized


def _required_workflow_modes_from_map() -> set[str]:
    phase_map = _load_ci_phase_map()
    return {f"--{row['mode']}" for rows in phase_map.values() for row in rows}


def _required_check_modes_from_map() -> set[str]:
    return _required_workflow_modes_from_map() | {"--lint", "--all", "--pre-commit"}


def _known_check_modes() -> set[str]:
    text = _read("scripts/lib/check/modes.sh")
    match = re.search(r"(?ms)^CHECK_MODES=\((?P<body>.*?)\)", text)
    assert match, "CHECK_MODES declaration missing in scripts/lib/check/modes.sh"
    body = match.group("body")
    parsed = shlex.split(body, comments=True, posix=True)
    return {f"--{mode}" for mode in parsed}


def _collect_check_modes(workflow_text: str) -> set[str]:
    modes: set[str] = set()
    for match in CHECK_COMMAND_PATTERN.finditer(workflow_text):
        args = match.group("args")
        modes.update(MODE_PATTERN.findall(args))
    return modes


@pytest.mark.script_regression
def test_ci_check_parity_required_modes_defined_in_check_script() -> None:
    known_modes = _known_check_modes()
    required_modes = _required_check_modes_from_map()
    missing = sorted(required_modes - known_modes)
    assert not missing, f"scripts/check.sh missing modes: {missing}"


@pytest.mark.script_regression
def test_ci_check_parity_workflow_uses_required_check_modes() -> None:
    lint_workflow = _read(".github/workflows/lint.yml")
    required_modes = _required_workflow_modes_from_map()
    workflow_modes = _collect_check_modes(lint_workflow)
    missing = sorted(required_modes - workflow_modes)
    assert not missing, f".github/workflows/lint.yml missing scripts/check.sh modes: {missing}"


@pytest.mark.script_regression
def test_ci_check_parity_workflow_removes_redundant_ad_hoc_phase_commands() -> None:
    lint_workflow = _read(".github/workflows/lint.yml")
    legacy_hits = [
        label
        for label, pattern in LEGACY_PHASE_COMMAND_PATTERNS.items()
        if re.search(pattern, lint_workflow)
    ]
    assert not legacy_hits, f"replace ad-hoc phase commands with scripts/check.sh modes: {legacy_hits}"


@pytest.mark.script_regression
def test_ci_check_parity_workflow_generated_phase_map_is_fresh() -> None:
    repo = _repo_root()
    run = subprocess.run(
        ["python3", "scripts/ci/generate-lint-workflow-phases.py", "--check"],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, (
        "generated lint workflow mapping is stale:\n"
        f"stdout:\n{run.stdout}\n"
        f"stderr:\n{run.stderr}\n"
    )
