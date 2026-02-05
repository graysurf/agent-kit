from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _script_path() -> Path:
    return _skill_root() / "scripts" / "playwright_cli.sh"


def _ensure_npx() -> None:
    if shutil.which("npx") is None:
        pytest.skip("npx not installed")


def test_tools_browser_playwright_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_browser_playwright_entrypoints_exist() -> None:
    assert_entrypoints_exist(_skill_root(), ["scripts/playwright_cli.sh"])


def test_tools_browser_playwright_help(tmp_path: Path) -> None:
    _ensure_npx()
    env = os.environ.copy()
    env.pop("PLAYWRIGHT_CLI_SESSION", None)
    proc = subprocess.run(
        [str(_script_path()), "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        env=env,
    )
    assert proc.returncode == 0, f"exit={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    haystack = (proc.stdout + proc.stderr).lower()
    assert "playwright-cli" in haystack or "usage:" in haystack
