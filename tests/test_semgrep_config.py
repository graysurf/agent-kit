from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Any, cast

from .conftest import repo_root


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

    semgrep_bin = Path(sys.executable).with_name("semgrep")
    if not semgrep_bin.exists():
        semgrep_on_path = which("semgrep")
        assert semgrep_on_path, "semgrep not found; install dev dependencies from requirements-dev.txt"
        semgrep_bin = Path(semgrep_on_path)

    completed = subprocess.run(
        [
            str(semgrep_bin),
            "scan",
            "--config",
            str(config),
            "--json",
            "--metrics=off",
            "--disable-version-check",
            str(fixture),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, f"semgrep scan failed:\n{completed.stderr}"

    payload_raw: Any = json.loads(completed.stdout)
    assert isinstance(payload_raw, dict), "unexpected semgrep JSON: expected an object payload"
    payload = cast(dict[str, Any], payload_raw)

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
