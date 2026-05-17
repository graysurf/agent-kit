from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_prompts_actionable_knowledge_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_actionable_knowledge_prompt_source_is_present() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    prompt = skill_root / "references" / "prompts" / "actionable-knowledge.md"
    text = prompt.read_text(encoding="utf-8")

    assert "argument-hint: question / concept / confusion" in text
    assert "USER QUESTION $ARGUMENTS" in text
    assert "CORE PRINCIPLES" in text
