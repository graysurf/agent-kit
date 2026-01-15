from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from shutil import which

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
                "# TODO: fixture",
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
                "# FIXME: fixture",
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
                "# HACK: fixture",
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

    payload = json.loads(completed.stdout)
    results = payload.get("results", [])
    assert isinstance(results, list), "unexpected semgrep JSON: missing results list"

    rule_ids = {r.get("check_id") for r in results if isinstance(r, dict)}

    expected = {
        "codex-kit.comment.todo",
        "codex-kit.comment.fixme",
        "codex-kit.comment.hack",
        "codex-kit.shell.typeset-empty-string-double-quotes",
        "codex-kit.shell.eval",
        "codex-kit.shell.curl-pipe-shell",
        "codex-kit.python.subprocess-shell-true",
        "codex-kit.python.os-system",
        "codex-kit.python.eval-exec",
    }
    missing = expected - {x for x in rule_ids if isinstance(x, str)}
    assert not missing, f"expected Semgrep rules not triggered: {sorted(missing)}"
