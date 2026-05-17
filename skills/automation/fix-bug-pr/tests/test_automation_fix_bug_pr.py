from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_automation_fix_bug_pr_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_automation_fix_bug_pr_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/bug-pr-resolve.sh",
            "scripts/bug-pr-patch.sh",
        ],
    )


def test_automation_fix_bug_pr_requires_test_first_evidence_gate() -> None:
    text = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "## Test-First Evidence Gate" in text
    assert "failing-test evidence or an explicit waiver" in text
    assert "before editing production behavior" in text
    assert "Change classification" in text
    assert "Failing test before fix" in text
    assert "Final validation" in text
    assert "Waiver reason" in text
