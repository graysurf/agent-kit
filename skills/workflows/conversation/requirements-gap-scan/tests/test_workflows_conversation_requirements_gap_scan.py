from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_conversation_requirements_gap_scan_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_workflows_conversation_requirements_gap_scan_explicit_first() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    assert "name: requirements-gap-scan" in text
    assert "old `ask-questions-if-underspecified` name" in text
    assert "explicit-first" in text
    assert (
        "Do not use this skill as the default behavior for ordinary implementation requests."
        in text
    )
    assert "gap-scan" in text
    assert "blocking" in text
    assert "Must Decide" in text
    assert "Suggested Defaults" in text
