from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_workflows_plan_create_plan_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def _skill_md_text() -> str:
    return (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")


def test_create_plan_requires_plan_tooling_executability_pass() -> None:
    text = _skill_md_text()
    assert "plan-tooling to-json --file docs/plans/<slug>-plan.md --sprint <n>" in text
    assert "plan-tooling batches --file docs/plans/<slug>-plan.md --sprint <n>" in text
    assert "--strategy auto --default-pr-grouping group --format json" in text
    assert "--pr-grouping group --strategy deterministic --pr-group ... --format json" in text
    assert "--pr-grouping per-sprint --strategy deterministic --format json" in text


def test_create_plan_documents_grouping_metadata_and_cross_sprint_policy() -> None:
    text = _skill_md_text()
    assert "Treat sprints as sequential integration gates" in text
    assert "do not imply cross-sprint execution parallelism." in text.lower()
    assert "`**PR grouping intent**: per-sprint|group`" in text
    assert "`**Execution Profile**: serial|parallel-xN`" in text
    assert "If `PR grouping intent` is `per-sprint`, do not declare parallel width `>1`." in text
