from __future__ import annotations

import subprocess

from .conftest import repo_root


def test_api_test_summary_help_mentions_hide_skipped_default_off() -> None:
    script = (
        repo_root()
        / "skills"
        / "tools"
        / "testing"
        / "api-test-runner"
        / "scripts"
        / "api-test-summary.sh"
    )
    completed = subprocess.run(
        [str(script), "--help"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "--hide-skipped" in completed.stderr
    assert "default: off" in completed.stderr

