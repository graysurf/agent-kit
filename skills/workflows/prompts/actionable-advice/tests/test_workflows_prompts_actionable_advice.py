from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_prompts_actionable_advice_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_actionable_advice_prompt_source_is_present() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    prompt = skill_root / "references" / "prompts" / "actionable-advice.md"
    text = prompt.read_text(encoding="utf-8")

    assert "argument-hint: question" in text
    assert "USER QUESTION $ARGUMENTS" in text
    assert "Recommendation" in text
