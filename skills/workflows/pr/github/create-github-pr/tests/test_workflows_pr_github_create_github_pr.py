from __future__ import annotations

import os
import subprocess
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_workflows_pr_github_create_github_pr_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_workflows_pr_github_create_github_pr_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/render_github_pr.sh",
        ],
    )


def _run_render(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "scripts" / "render_github_pr.sh"
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [str(script), *args],
        text=True,
        capture_output=True,
        check=False,
        env=run_env,
    )


def _skill_md_text() -> str:
    return (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")


def test_render_github_pr_outputs_feature_template_sections() -> None:
    result = _run_render("--kind", "feature", "--pr")
    assert result.returncode == 0, result.stderr
    assert "## Summary" in result.stdout
    assert "## Changes" in result.stdout
    assert "## Test-First Evidence" in result.stdout
    assert "Change classification:" in result.stdout
    assert "Failing test before fix:" in result.stdout
    assert "Final validation:" in result.stdout
    assert "Waiver reason" in result.stdout
    assert "## Testing" in result.stdout
    assert "{{OPTIONAL_SECTIONS}}" not in result.stdout
    assert "## Problem" not in result.stdout


def test_render_github_pr_outputs_bug_template_sections() -> None:
    result = _run_render("--kind", "bug", "--pr")
    assert result.returncode == 0, result.stderr
    assert "## Problem" in result.stdout
    assert "## Reproduction" in result.stdout
    assert "## Issues Found" in result.stdout
    assert "## Fix Approach" in result.stdout
    assert "## Test-First Evidence" in result.stdout
    assert "Change classification:" in result.stdout
    assert "Failing test before fix:" in result.stdout
    assert "Final validation:" in result.stdout
    assert "Waiver reason" in result.stdout
    assert "## Changes" not in result.stdout


def test_render_github_pr_outputs_kind_specific_assistant_templates() -> None:
    feature_result = _run_render("--kind", "feature", "--output")
    bug_result = _run_render("--kind", "bug", "--output")
    assert feature_result.returncode == 0, feature_result.stderr
    assert bug_result.returncode == 0, bug_result.stderr
    assert "## Feature Summary" in feature_result.stdout
    assert "## Issues List" in bug_result.stdout
    assert "## PR Link" in feature_result.stdout
    assert "## PR Link" in bug_result.stdout


def test_render_github_pr_requires_kind_and_rejects_unknown_kind() -> None:
    missing_kind = _run_render("--pr")
    unknown_kind = _run_render("--kind", "docs", "--pr")
    assert missing_kind.returncode == 1
    assert "error: --kind is required" in missing_kind.stderr
    assert unknown_kind.returncode == 1
    assert "error: unsupported kind: docs" in unknown_kind.stderr


def test_render_github_pr_rejects_unknown_flags() -> None:
    result = _run_render("--kind", "feature", "--pr", "--unexpected-flag")
    assert result.returncode == 1
    assert "Unknown option: --unexpected-flag" in result.stderr


def test_create_github_pr_skill_declares_audited_marker_and_gh_create() -> None:
    text = _skill_md_text()
    assert "AGENT_KIT_PR_SKILL=create-github-pr" in text
    assert "gh pr create" in text
    assert "`kind`: `feature` or `bug`" in text


def test_create_github_pr_skill_keeps_provider_contract_explicit() -> None:
    text = _skill_md_text()
    assert "GitHub PR" in text
    assert "`gh`" in text
    assert "Do not derive the PR title/body from `git log -1 --pretty=%B`" in text
    assert "feature` bodies must include Summary, Changes, Test-First Evidence, Testing, and Risk/Notes" in text
    assert (
        "bug` bodies must include Summary, Problem, Reproduction, Issues Found, Fix Approach, "
        "Test-First Evidence, Testing, and Risk/Notes"
    ) in text
    assert "Change classification" in text
    assert "Failing test before fix" in text
    assert "Final validation" in text
    assert "Waiver reason" in text
