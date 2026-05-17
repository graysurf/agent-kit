from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_prompts_parallel_first_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_parallel_first_prompt_source_is_present() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    prompt = skill_root / "references" / "prompts" / "parallel-first.md"
    text = prompt.read_text(encoding="utf-8")

    assert "argument-hint: preferences (optional)" in text
    assert "Enable **parallel-first mode**" in text
    assert "PARALLEL_DELEGATION_PROTOCOL.md" in text
    assert "requirements-gap-scan" in text
