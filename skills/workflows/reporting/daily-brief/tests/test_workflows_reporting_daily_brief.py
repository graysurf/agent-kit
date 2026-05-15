from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract, repo_root


def test_workflows_reporting_daily_brief_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_workflows_reporting_daily_brief_orchestrates_topic_radar() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    assert "instruction-first workflow" in text
    assert "$AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh" in text
    assert "--preset ai-news --format json" in text
    assert "--refresh" in text
    assert "--preset radar --format json" in text
    assert "Do not split source fetchers" in text
    assert "Match the user's language" in text
    assert "source-health" in text
    assert "memory" in text


def test_workflows_reporting_daily_brief_declares_skill_boundaries() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

    assert "`daily-brief` is the user-facing daily entrypoint" in text
    assert "`topic-radar` is the lower-level radar engine" in text
    assert "`polymarket-readonly` is the market-only helper" in text
    assert "Use `daily-brief` when" in text
    assert "Use `topic-radar` directly when" in text
    assert "Use `polymarket-readonly` directly when" in text


def test_workflows_reporting_daily_brief_is_listed_in_catalog() -> None:
    readme = (repo_root() / "README.md").read_text(encoding="utf-8")

    assert "[daily-brief](./skills/workflows/reporting/daily-brief/)" in readme
    assert "topic-radar JSON" in readme
