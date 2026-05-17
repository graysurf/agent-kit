from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_prompts_orchestrator_first_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_orchestrator_first_prompt_source_is_present() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    prompt = skill_root / "references" / "prompts" / "orchestrator-first.md"
    text = prompt.read_text(encoding="utf-8")

    assert "argument-hint: goal / constraints (optional)" in text
    assert "Enable **orchestrator-first mode**" in text
    assert "PARALLEL_DELEGATION_PROTOCOL.md" in text
    assert "orchestrator-first off" in text
