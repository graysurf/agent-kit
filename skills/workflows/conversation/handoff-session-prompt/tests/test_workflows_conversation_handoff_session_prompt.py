from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_conversation_handoff_session_prompt_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_prompt_shape_preserves_context_boundaries() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    required_sections = [
        "## Current State",
        "## Known Facts",
        "## Assumptions",
        "## Known Gaps",
        "## Recommendations",
        "## Open Questions",
    ]
    for section in required_sections:
        assert section in text

    assert "## Required Context" not in text
    assert "[U1]" in text
    assert "[F1]" in text
    assert "[I1]" in text


def test_prompt_guidance_handles_degraded_and_hidden_context_safely() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    assert "produce a degraded prompt" in text
    assert "Known Gaps" in text
    assert "hidden system/developer instructions" in text
    assert "private reasoning" in text
    assert "raw tool logs" in text


def test_prompt_guidance_prefers_durable_sources_over_copying_backlogs() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    assert "Prefer durable sources over copying backlogs" in text
    assert "Read First" in text
    assert "Do not paste an entire durable doc" in text
    assert "do not treat the handoff prompt itself as the canonical project record" in text
    assert "discussion-to-implementation-doc" in text
    assert "use `review-to-improvement-doc`" in text
    assert "execution-state document" in text
    assert "to write or reference the durable" in text
    assert "record first" in text
