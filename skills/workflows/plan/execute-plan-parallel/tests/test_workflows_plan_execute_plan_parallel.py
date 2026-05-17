from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_workflows_plan_execute_plan_parallel_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_execute_plan_parallel_requires_test_first_evidence_gate() -> None:
    text = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "## Test-First Evidence Gate" in text
    assert "failing-test evidence or an explicit waiver" in text
    assert "before editing production behavior" in text
    assert "Change classification" in text
    assert "Failing test before fix" in text
    assert "Final validation" in text
    assert "Waiver reason" in text
