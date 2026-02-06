from __future__ import annotations

import subprocess
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_workflows_pr_feature_create_feature_pr_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_workflows_pr_feature_create_feature_pr_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/render_feature_pr.sh",
        ],
    )


def _run_render(*args: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "scripts" / "render_feature_pr.sh"
    return subprocess.run([str(script), *args], text=True, capture_output=True, check=False)


def test_render_feature_pr_omits_optional_sections_when_missing() -> None:
    result = _run_render("--pr")
    assert result.returncode == 0, result.stderr
    assert "## Progress" not in result.stdout
    assert "## Planning PR" not in result.stdout
    assert "## Summary" in result.stdout
    assert "## Changes" in result.stdout


def test_render_feature_pr_includes_optional_sections_when_provided() -> None:
    result = _run_render(
        "--pr",
        "--progress-url",
        "https://github.com/org/repo/blob/feat-branch/docs/progress/20260206_slug.md",
        "--planning-pr",
        "#123",
    )
    assert result.returncode == 0, result.stderr
    assert "## Progress" in result.stdout
    assert "## Planning PR" in result.stdout
    assert "- #123" in result.stdout
    assert "https://github.com/org/repo/blob/feat-branch/docs/progress/20260206_slug.md" in result.stdout
