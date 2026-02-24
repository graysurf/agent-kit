from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_workflows_plan_create_plan_rigorous_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def _skill_md_text() -> str:
    return (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(encoding="utf-8")


def test_create_plan_rigorous_forbids_cross_sprint_parallel_execution() -> None:
    text = _skill_md_text()
    assert "do not plan cross-sprint execution parallelism." in text.lower()
    assert "Do not schedule cross-sprint execution parallelism." in text
    assert "Treat sprints as sequential integration gates" in text


def test_create_plan_rigorous_defines_pr_and_sprint_complexity_guardrails() -> None:
    text = _skill_md_text()
    assert "PR complexity target is `2-5`; preferred max is `6`." in text
    assert "PR complexity `7-8` is an exception and requires explicit justification" in text
    assert "PR complexity `>8` should be split before execution planning." in text
    assert "CriticalPathComplexity" in text
    assert "Do not use `TotalComplexity` alone as the sizing signal" in text
    assert "`serial`: target `2-4` tasks, `TotalComplexity 8-16`" in text
    assert "`parallel-x2`: target `3-5` tasks, `TotalComplexity 12-22`" in text
    assert "`parallel-x3`: target `4-6` tasks, `TotalComplexity 16-24`" in text


def test_create_plan_rigorous_high_complexity_task_policy_requires_split_or_dedicated_lane() -> None:
    text = _skill_md_text()
    assert "For a task with complexity `>=7`, try to split first" in text
    assert "keep it as a dedicated lane and dedicated PR" in text
    assert "at most one task with complexity `>=7` per sprint" in text
