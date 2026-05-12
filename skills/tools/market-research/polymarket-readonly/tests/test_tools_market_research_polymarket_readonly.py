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
