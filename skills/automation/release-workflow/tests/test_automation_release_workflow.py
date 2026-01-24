from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_automation_release_workflow_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_automation_release_workflow_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/audit-changelog.zsh",
            "scripts/release-audit.sh",
            "scripts/release-find-guide.sh",
            "scripts/release-notes-from-changelog.sh",
            "scripts/release-resolve.sh",
            "scripts/release-scaffold-entry.sh",
        ],
    )
