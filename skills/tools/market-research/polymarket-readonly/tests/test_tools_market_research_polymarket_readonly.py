from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def test_tools_market_research_polymarket_readonly_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_market_research_polymarket_readonly_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(skill_root, ["scripts/polymarket-readonly.sh"])


def test_tools_market_research_polymarket_readonly_declares_readonly_boundary() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    options_text = (skill_root / "references" / "mcp-options.md").read_text(encoding="utf-8")

    assert "polymarket-mcp-server" in skill_text
    assert "Never request, configure, or use wallet private" in skill_text
    assert "order cancellation" in skill_text
    assert "intentionally read-only" in options_text
    assert "Local Codex config should use no `env` block" in options_text
    assert "gamma_search_public" in options_text
    assert "expects `q=`" in options_text


def test_tools_market_research_polymarket_readonly_blocks_trading_env() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "polymarket-readonly.sh"
    env = os.environ.copy()
    env["POLYMARKET_PRIVATE_KEY"] = "not-a-real-key"

    proc = subprocess.run(
        [str(script), "--check-env"],
        text=True,
        capture_output=True,
        env=env,
    )

    assert proc.returncode == 3
    assert "POLYMARKET_PRIVATE_KEY" in proc.stderr


def test_tools_market_research_polymarket_readonly_usage_mentions_trending() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "polymarket-readonly.sh"

    proc = subprocess.run(
        [str(script), "--help"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0
    assert "--trending" in proc.stdout
    assert "--days <n>" in proc.stdout
    assert "--scope events|markets|both" in proc.stdout
    assert "--format json|markdown" in proc.stdout
    assert "--report daily|weekly" in proc.stdout


def test_tools_market_research_polymarket_readonly_search_uses_rest_q_param() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[5]
    script = skill_root / "scripts" / "polymarket-readonly.sh"
    env = os.environ.copy()
    env["PATH"] = f"{repo_root / 'tests' / 'stubs' / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env["CODEX_CURL_STUB_MODE_ENABLED"] = "true"
    env["CODEX_CURL_STUB_BODY"] = json.dumps(
        {
            "events": [
                {
                    "id": "1",
                    "slug": "sample-event",
                    "title": "Sample Event",
                    "active": True,
                    "closed": False,
                    "markets": [
                        {
                            "id": "2",
                            "slug": "sample-market",
                            "question": "Sample market?",
                            "active": True,
                            "closed": False,
                            "clobTokenIds": '["1", "2"]',
                        }
                    ],
                }
            ],
            "pagination": {"totalResults": 1},
        }
    )

    proc = subprocess.run(
        [str(script), "--search", "ai", "--limit", "5"],
        text=True,
        capture_output=True,
        env=env,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["source"] == "gamma-api/public-search"
    assert payload["query"] == "ai"
    assert payload["events"][0]["slug"] == "sample-event"
    assert payload["markets"][0]["slug"] == "sample-market"


def test_tools_market_research_polymarket_readonly_trending_blocks_trading_env() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "polymarket-readonly.sh"
    env = os.environ.copy()
    env["POLYMARKET_PRIVATE_KEY"] = "not-a-real-key"

    proc = subprocess.run(
        [str(script), "--trending"],
        text=True,
        capture_output=True,
        env=env,
    )

    assert proc.returncode == 3
    assert "POLYMARKET_PRIVATE_KEY" in proc.stderr


def test_tools_market_research_polymarket_readonly_report_blocks_trading_env() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    script = skill_root / "scripts" / "polymarket-readonly.sh"
    env = os.environ.copy()
    env["POLYMARKET_PRIVATE_KEY"] = "not-a-real-key"

    proc = subprocess.run(
        [str(script), "--report", "daily"],
        text=True,
        capture_output=True,
        env=env,
    )

    assert proc.returncode == 3
    assert "POLYMARKET_PRIVATE_KEY" in proc.stderr


def test_tools_market_research_polymarket_readonly_trending_defaults_to_gamma_event_proxy(
    tmp_path: Path,
) -> None:
    skill_root = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[5]
    script = skill_root / "scripts" / "polymarket-readonly.sh"
    env = os.environ.copy()
    env["PATH"] = f"{repo_root / 'tests' / 'stubs' / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env["CODEX_CURL_STUB_MODE_ENABLED"] = "true"
    env["CODEX_STUB_LOG_DIR"] = str(tmp_path)
    env["CODEX_CURL_STUB_BODY"] = json.dumps(
        [
            {
                "id": "1",
                "slug": "sample-event",
                "title": "Sample Event",
                "active": True,
                "closed": False,
                "volume1wk": 123.45,
                "volume24hr": 12.3,
                "volume1mo": 456.78,
            }
        ]
    )

    proc = subprocess.run(
        [str(script), "--trending"],
        text=True,
        capture_output=True,
        env=env,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["source"] == "gamma-api/events"
    assert payload["scope"] == "events"
    assert payload["windowDays"] == 3
    assert payload["rankingMetric"] == "volume1wk"
    assert payload["rankingMode"] == "proxy"
    assert payload["results"][0]["slug"] == "sample-event"
    assert payload["results"][0]["rankingValue"] == 123.45

    curl_log = (tmp_path / "curl.calls.txt").read_text(encoding="utf-8")
    assert "https://gamma-api.polymarket.com/events" in curl_log
    assert "--data-urlencode active=true" in curl_log
    assert "--data-urlencode closed=false" in curl_log
    assert "--data-urlencode limit=10" in curl_log
    assert "--data-urlencode order=volume1wk" in curl_log
    assert "--data-urlencode ascending=false" in curl_log


def test_tools_market_research_polymarket_readonly_daily_report_defaults_to_markdown_both(
    tmp_path: Path,
) -> None:
    skill_root = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[5]
    script = skill_root / "scripts" / "polymarket-readonly.sh"
    env = os.environ.copy()
    env["PATH"] = f"{repo_root / 'tests' / 'stubs' / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env["CODEX_CURL_STUB_MODE_ENABLED"] = "true"
    env["CODEX_STUB_LOG_DIR"] = str(tmp_path)
    env["CODEX_CURL_STUB_BODY"] = json.dumps(
        [
            {
                "id": "1",
                "slug": "sample-topic",
                "question": "Sample question?",
                "active": True,
                "closed": False,
                "volume24hr": 12.3,
                "volume1wk": 123.45,
                "liquidity": 456.7,
            }
        ]
    )

    proc = subprocess.run(
        [str(script), "--report", "daily", "--limit", "1"],
        text=True,
        capture_output=True,
        env=env,
    )

    assert proc.returncode == 0
    assert "# Polymarket Daily Trends" in proc.stdout
    assert "- Window: 1 day(s)" in proc.stdout
    assert "- Ranking: volume24hr (native)" in proc.stdout
    assert "## Hot Topics" in proc.stdout
    assert "## Hot Questions" in proc.stdout
    assert "Read-only public Gamma API lookup" in proc.stdout

    curl_log = (tmp_path / "curl.calls.txt").read_text(encoding="utf-8")
    assert "https://gamma-api.polymarket.com/events" in curl_log
    assert "https://gamma-api.polymarket.com/markets" in curl_log
    assert curl_log.count("--data-urlencode order=volume24hr") == 2
    assert curl_log.count("--data-urlencode limit=1") == 2


def test_tools_market_research_polymarket_readonly_weekly_report_json_scope_markets() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[5]
    script = skill_root / "scripts" / "polymarket-readonly.sh"
    env = os.environ.copy()
    env["PATH"] = f"{repo_root / 'tests' / 'stubs' / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env["CODEX_CURL_STUB_MODE_ENABLED"] = "true"
    env["CODEX_CURL_STUB_BODY"] = json.dumps(
        [
            {
                "id": "1",
                "slug": "sample-market",
                "question": "Sample market?",
                "active": True,
                "closed": False,
                "volume1wk": 123.45,
            }
        ]
    )

    proc = subprocess.run(
        [str(script), "--report", "weekly", "--scope", "markets", "--format", "json"],
        text=True,
        capture_output=True,
        env=env,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["report"] == "weekly"
    assert payload["source"] == "gamma-api/markets"
    assert payload["scope"] == "markets"
    assert payload["windowDays"] == 7
    assert payload["rankingMetric"] == "volume1wk"
    assert payload["rankingMode"] == "native"
    assert payload["results"][0]["question"] == "Sample market?"
    assert payload["results"][0]["url"] == "https://polymarket.com/market/sample-market"
