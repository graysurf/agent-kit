from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_pr_progress_create_progress_pr_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)
