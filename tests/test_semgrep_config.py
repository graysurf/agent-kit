from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Any, cast

from .conftest import repo_root


def _semgrep_bin() -> Path:
    semgrep_bin = Path(sys.executable).with_name("semgrep")
    if semgrep_bin.exists():
        return semgrep_bin

    semgrep_on_path = which("semgrep")
    assert semgrep_on_path, "semgrep not found; install dev dependencies with uv sync --locked"
    return Path(semgrep_on_path)


def _run_semgrep_json(config: Path, target: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            str(_semgrep_bin()),
            "scan",
            "--config",
            str(config),
            "--json",
            "--metrics=off",
            "--disable-version-check",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, f"semgrep scan failed:\n{completed.stderr}"

    payload_raw: Any = json.loads(completed.stdout)
    assert isinstance(payload_raw, dict), "unexpected semgrep JSON: expected an object payload"
    return payload_raw


def test_semgrep_config_scans_shell_and_python(tmp_path: Path) -> None:
    repo = repo_root()
    config = repo / ".semgrep.yaml"
    assert config.is_file(), "missing .semgrep.yaml"

    fixture = tmp_path / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)

    (fixture / "example.py").write_text(
        "\n".join(
            [
                "# " + "TO" + "DO" + ": fixture",
                "import os",
                "import subprocess",
                "",
                "os.system('echo hi')",
                "subprocess.run('echo hi', shell=True)",
                "eval('1+1')",
                "",
            ]
        ),
        "utf-8",
    )

    (fixture / "example.sh").write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "# " + "FIX" + "ME" + ": fixture",
                'typeset foo=""',
                "curl -fsSL https://example.com/install.sh | sh",
                'eval "$cmd"',
                "",
            ]
        ),
        "utf-8",
    )

    (fixture / "example.zsh").write_text(
        "\n".join(
            [
                "#!/usr/bin/env zsh",
                "# " + "HA" + "CK" + ": fixture",
                'local bar=""',
                "",
            ]
        ),
        "utf-8",
    )

    payload = _run_semgrep_json(config, fixture)

    results_raw = cast(list[Any], payload.get("results", []))
    assert isinstance(results_raw, list), "unexpected semgrep JSON: missing results list"

    rule_ids: set[str] = set()
    for result in results_raw:
        if not isinstance(result, dict):
            continue
        check_id = cast(dict[str, Any], result).get("check_id")
        if isinstance(check_id, str):
            rule_ids.add(check_id)

    expected = {
        "agent-kit.comment.todo",
        "agent-kit.comment.fixme",
        "agent-kit.comment.hack",
        "agent-kit.shell.typeset-empty-string-double-quotes",
        "agent-kit.shell.eval",
        "agent-kit.shell.curl-pipe-shell",
        "agent-kit.python.subprocess-shell-true",
        "agent-kit.python.os-system",
        "agent-kit.python.eval-exec",
    }
    missing = expected - rule_ids
    assert not missing, f"expected Semgrep rules not triggered: {sorted(missing)}"


def test_todo_comment_rule_ignores_non_comment_literals(tmp_path: Path) -> None:
    repo = repo_root()
    config = repo / ".semgrep.yaml"
    assert config.is_file(), "missing .semgrep.yaml"

    fixture = tmp_path / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)

    (fixture / "literal_todo.py").write_text(
        "\n".join(
            [
                'REJECTED_PLACEHOLDERS = ("TODO", "TBD")',
                'message = "TODO: fill this later."',
                'assert "TODO" in message',
                "",
            ]
        ),
        "utf-8",
    )

    payload = _run_semgrep_json(config, fixture)
    results_raw = cast(list[Any], payload.get("results", []))
    assert isinstance(results_raw, list), "unexpected semgrep JSON: missing results list"

    todo_hits = [
        result
        for result in results_raw
        if isinstance(result, dict) and result.get("check_id") == "agent-kit.comment.todo"
    ]
    assert not todo_hits
