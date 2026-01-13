from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from .conftest import default_env, repo_root


def run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=default_env(cwd),
        text=True,
        capture_output=True,
        timeout=10,
    )


def test_validate_skill_contracts_passes_for_repo():
    repo = repo_root()
    result = run(["bash", str(repo / "scripts" / "validate_skill_contracts.sh")], cwd=repo)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def test_validate_skill_contracts_fails_for_invalid_contract(tmp_path: Path):
    fixture = tmp_path / "bad-skill.md"
    fixture.write_text(
        "\n".join(
            [
                "# Fixture Skill",
                "",
                "## Contract",
                "",
                "Prereqs:",
                "- N/A",
                "",
                "Inputs:",
                "- N/A",
                "",
                "Outputs:",
                "- N/A",
                "",
                "Exit codes:",
                "- N/A",
                "",
                "# Missing Failure modes:",
                "",
            ]
        )
        + "\n",
        "utf-8",
    )

    repo = repo_root()
    result = run(
        ["bash", str(repo / "scripts" / "validate_skill_contracts.sh"), "--file", str(fixture)],
        cwd=repo,
    )
    assert result.returncode != 0
    assert "Failure modes" in result.stderr


def test_validate_progress_index_passes_for_repo():
    repo = repo_root()
    script = repo / "skills" / "workflows" / "pr" / "progress" / "create-progress-pr" / "scripts" / "validate_progress_index.sh"
    result = run(["bash", str(script)], cwd=repo)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def test_validate_progress_index_fails_for_invalid_pr_cell(tmp_path: Path):
    repo = repo_root()
    original = repo / "docs" / "progress" / "README.md"
    mutated = tmp_path / "progress-readme.md"
    mutated.write_text(original.read_text("utf-8"), "utf-8")

    lines = mutated.read_text("utf-8").splitlines()
    try:
        in_progress_idx = next(i for i, line in enumerate(lines) if line.strip() == "## In progress")
        archived_idx = next(i for i, line in enumerate(lines) if line.strip() == "## Archived")
    except StopIteration as exc:
        raise AssertionError("docs/progress/README.md missing required headings") from exc

    in_sep = None
    for i in range(in_progress_idx, archived_idx):
        if lines[i].startswith("| ---"):
            in_sep = i
            break

    assert in_sep is not None, "docs/progress/README.md missing In progress table separator"

    mutated_row_idx = None
    for i in range(in_sep + 1, archived_idx):
        if not lines[i].startswith("|") or lines[i].startswith("| ---"):
            continue
        parts = [p.strip() for p in lines[i].strip().strip("|").split("|")]
        if len(parts) == 3:
            mutated_row_idx = i
            break

    if mutated_row_idx is None:
        lines.insert(in_sep + 1, "| 2099-01-01 | Fixture | NOT_A_LINK |")
    else:
        parts = [p.strip() for p in lines[mutated_row_idx].strip().strip("|").split("|")]
        parts[2] = "NOT_A_LINK"
        lines[mutated_row_idx] = f"| {parts[0]} | {parts[1]} | {parts[2]} |"

    mutated.write_text("\n".join(lines).rstrip() + "\n", "utf-8")

    script = repo / "skills" / "workflows" / "pr" / "progress" / "create-progress-pr" / "scripts" / "validate_progress_index.sh"
    result = run(["bash", str(script), "--file", str(mutated)], cwd=repo)
    assert result.returncode != 0
    assert "invalid PR cell" in result.stderr
