from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_conversation_review_to_improvement_doc_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_review_to_improvement_doc_defines_artifact_boundary() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    assert "durable repo-local document" in text
    assert "Do not turn it into a phased implementation plan" in text
    assert "Do not turn it into a handoff prompt" in text
    assert "Avoid `docs/plans/` unless the artifact is a real implementation plan" in text


def test_review_to_improvement_doc_requires_findings_and_discoverability() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    assert "findings table with priority, issue, evidence, fix location, and acceptance" in text
    assert "runtime vs test/harness vs docs" in text
    assert "Update the nearest docs index or README" in text
    assert "`Read First`" in text
