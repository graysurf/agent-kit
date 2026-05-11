from __future__ import annotations

import os
import subprocess
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_workflows_mr_gitlab_create_gitlab_mr_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_workflows_mr_gitlab_create_gitlab_mr_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/render_gitlab_mr.sh",
        ],
    )


def _run_render(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "scripts" / "render_gitlab_mr.sh"
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


def test_render_gitlab_mr_outputs_required_sections() -> None:
    result = _run_render("--mr")
    assert result.returncode == 0, result.stderr
    assert "## Summary" in result.stdout
    assert "## Testing" in result.stdout
    assert "## Source Branch Policy" in result.stdout
    assert "remove source branch on merge: `false`" in result.stdout


def test_render_gitlab_mr_outputs_assistant_template() -> None:
    result = _run_render("--output")
    assert result.returncode == 0, result.stderr
    assert "## MR Summary" in result.stdout
    assert "## MR Link" in result.stdout


def test_render_gitlab_mr_rejects_unknown_flags() -> None:
    result = _run_render("--mr", "--unexpected-flag")
    assert result.returncode == 1
    assert "Unknown option: --unexpected-flag" in result.stderr


def test_create_gitlab_mr_skill_declares_audited_marker_and_glab_create() -> None:
    text = _skill_md_text()
    assert "AGENT_KIT_PR_SKILL=create-gitlab-mr" in text
    assert "glab mr create" in text
    assert "--remove-source-branch=false" in text


def test_create_gitlab_mr_skill_keeps_gitlab_separate_from_github_pr_contract() -> None:
    text = _skill_md_text()
    assert "GitLab MR" in text
    assert "`glab`" in text
    assert "Do not derive the MR title/body from `git log -1 --pretty=%B`" in text
