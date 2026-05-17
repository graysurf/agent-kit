from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


ROOT = Path(__file__).resolve().parents[1]


SKILLS = {
    "browser-session": ROOT / "skills/tools/browser/evidence/browser-session",
    "docs-impact": ROOT / "skills/tools/workflow-evidence/docs-impact",
    "review-evidence": ROOT / "skills/tools/workflow-evidence/review-evidence",
    "canary-check": ROOT / "skills/tools/workflow-evidence/canary-check",
    "model-cross-check": ROOT / "skills/tools/workflow-evidence/model-cross-check",
}


def _text(name: str) -> str:
    return (SKILLS[name] / "SKILL.md").read_text(encoding="utf-8")


def test_agent_workflow_primitive_skill_contracts() -> None:
    for skill_root in SKILLS.values():
        assert_skill_contract(skill_root)


def test_agent_workflow_primitive_skills_document_release_boundary() -> None:
    for name in SKILLS:
        text = _text(name)
        assert "`nils-cli 0.8.4` or newer" in text
        assert "`0.8.4` is the release that includes `nils-agent-workflow-primitives`" in text
        assert "validated local `nils-cli` checkout" in text
        assert "PATH binary is absent or too old" in text
        assert "-p nils-agent-workflow-primitives --bin" in text
        assert f"{name} completion <bash|zsh>" in text


def test_agent_workflow_primitive_skills_document_artifacts_and_json_contracts() -> None:
    expectations = {
        "browser-session": ["browser-session.json", "cli.browser-session.verify.v1"],
        "docs-impact": ["cli.docs-impact.scan.v1", "suggested_review"],
        "review-evidence": ["review-evidence.json", "cli.review-evidence.verify.v1"],
        "canary-check": ["canary-check.json", "cli.canary-check.run.v1"],
        "model-cross-check": ["model-cross-check.json", "cli.model-cross-check.verify.v1"],
    }

    for name, needles in expectations.items():
        text = _text(name)
        for needle in needles:
            assert needle in text
