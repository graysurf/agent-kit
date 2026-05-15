from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def load_topic_radar_module() -> ModuleType:
    skill_root = Path(__file__).resolve().parents[1]
    module_path = skill_root / "bin" / "topic_radar.py"
    spec = importlib.util.spec_from_file_location("topic_radar_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tools_market_research_topic_radar_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_market_research_topic_radar_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(skill_root, ["scripts/topic-radar.sh"])


def test_tools_market_research_topic_radar_contract_declares_sources() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    strategy_text = (skill_root / "references" / "source-strategy.md").read_text(encoding="utf-8")

    assert "polymarket" in skill_text
    assert "Hacker News" in skill_text
    assert "GitHub" in skill_text
    assert "arXiv" in skill_text
    assert "Hugging Face" in skill_text
    assert "daily-brief" in skill_text
    assert "cross-source duplication bonus" in strategy_text
    assert "Relationship to Daily Brief" in strategy_text
    assert "Do not present the score as objective importance" in strategy_text


def test_tools_market_research_topic_radar_ai_topic_uses_word_boundary() -> None:
    module = load_topic_radar_module()
    false_match = module.RadarItem(source="hn", title="Climate-resilient homes reduce air conditioner use", url="")
    true_match = module.RadarItem(source="hn", title="AI safety update for coding agents", url="")
    dotted_match = module.RadarItem(source="hn", title="A.I. safety talks begin", url="")

    assert module.interest_match_score(false_match, ["AI"]) == 0
    assert module.interest_match_score(true_match, ["AI"]) > 0
    assert module.interest_match_score(dotted_match, ["AI"]) > 0


def test_tools_market_research_topic_radar_help_mentions_report_options() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run([str(script), "--help"], text=True, capture_output=True)

    assert proc.returncode == 0
    assert "--topic" in proc.stdout
    assert "--preset" in proc.stdout
    assert "--sources" in proc.stdout
    assert "--polymarket-mcp-json" in proc.stdout
    assert "--report" in proc.stdout
    assert "--from" in proc.stdout
    assert "--to" in proc.stdout
    assert "--month" in proc.stdout
    assert "--brief" in proc.stdout
    assert "--cache-ttl-minutes" in proc.stdout
    assert "--news-provider" in proc.stdout
    assert "--refresh" in proc.stdout
    assert "--sample" in proc.stdout


def test_tools_market_research_topic_radar_sample_json_is_structured() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--format", "json", "--limit", "3"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["preset"] == "radar"
    assert payload["profile"] == "terry-ai-tech"
    assert payload["sample"] is True
    assert payload["ranking"]["mode"] == "heuristic"
    assert payload["window"]["mode"] == "rolling"
    assert payload["window"]["days"] == payload["windowDays"]
    assert payload["cache"]["enabled"] is False
    assert len(payload["items"]) == 3
    assert "robotics" in payload["topics"]
    assert {"polymarket", "hn", "github", "arxiv", "hf", "official", "news"} <= set(payload["sections"])


def test_tools_market_research_topic_radar_sample_markdown_has_sections() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--format", "markdown", "--report", "weekly", "--limit", "2"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    assert "# AI/Tech Topic Radar Weekly" in proc.stdout
    assert "## Top Signals" in proc.stdout
    assert "## Source Sections" in proc.stdout
    assert "### Market Attention" in proc.stdout
    assert "### Research" in proc.stdout
    assert "Scores are heuristic triage signals" in proc.stdout


def test_tools_market_research_topic_radar_ai_news_preset_is_brief_and_focused() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--preset", "ai-news", "--format", "json"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["preset"] == "ai-news"
    assert payload["brief"]["enabled"] is True
    assert payload["newsProvider"] == "google"
    assert payload["sources"] == ["official", "news", "hn"]
    assert payload["windowDays"] == 5
    assert payload["window"]["label"] == "last 5 day(s)"
    assert set(payload["sections"]) == {"official", "news", "hn"}
    assert payload["brief"]["clusters"]


def test_tools_market_research_topic_radar_month_window_sets_fixed_metadata() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--preset", "ai-news", "--month", "2026-02", "--format", "json"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["report"] == "monthly"
    assert payload["windowDays"] == 28
    assert payload["window"] == {
        "mode": "fixed",
        "label": "2026-02",
        "start": "2026-02-01",
        "end": "2026-02-28",
        "days": 28,
        "complete": True,
    }


def test_tools_market_research_topic_radar_from_to_window_is_inclusive() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [
            str(script),
            "--sample",
            "--from",
            "2026-05-01",
            "--to",
            "2026-05-15",
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["windowDays"] == 15
    assert payload["window"]["mode"] == "fixed"
    assert payload["window"]["label"] == "2026-05-01..2026-05-15"
    assert payload["window"]["start"] == "2026-05-01"
    assert payload["window"]["end"] == "2026-05-15"


def test_tools_market_research_topic_radar_rejects_partial_fixed_window() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--from", "2026-05-01"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 2
    assert "--from and --to" in proc.stderr


def test_tools_market_research_topic_radar_ai_news_markdown_has_brief() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--preset", "ai-news", "--format", "markdown"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    assert "Preset: `ai-news`" in proc.stdout
    assert "## Brief" in proc.stdout
    assert "### Agents And Developer Tools" in proc.stdout
    assert "### Mainstream Coverage" in proc.stdout


def test_tools_market_research_topic_radar_rejects_unknown_source() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--sources", "unknown"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 2
    assert "unknown source" in proc.stderr


def test_tools_market_research_topic_radar_accepts_legacy_ai_tech_profile() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"

    proc = subprocess.run(
        [str(script), "--sample", "--profile", "ai-tech", "--format", "json", "--limit", "1"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["profile"] == "ai-tech"
    assert "developer tools" in payload["topics"]


def test_tools_market_research_topic_radar_reads_polymarket_mcp_json(tmp_path: Path) -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "topic-radar.sh"
    mcp_payload = {
        "events": [
            {
                "id": "event-1",
                "slug": "major-ai-model-release",
                "title": "Will a major AI lab release a new model this month?",
                "volume24hr": 12345,
                "markets": [
                    {
                        "id": "market-1",
                        "slug": "openai-frontier-model-this-month",
                        "question": "Will OpenAI release a frontier model this month?",
                        "volume1wk": 5000,
                    }
                ],
            }
        ]
    }
    mcp_path = tmp_path / "polymarket-mcp.json"
    mcp_path.write_text(json.dumps(mcp_payload), encoding="utf-8")

    proc = subprocess.run(
        [
            str(script),
            "--sources",
            "polymarket",
            "--polymarket-mcp-json",
            str(mcp_path),
            "--polymarket-fallback",
            "none",
            "--format",
            "json",
            "--limit",
            "3",
        ],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert not payload["errors"]
    assert len(payload["items"]) == 2
    assert payload["items"][0]["source"] == "polymarket"
    assert payload["items"][0]["sourceDetail"].startswith("polymarket-mcp")
    assert "MCP" in payload["items"][0]["reason"]
