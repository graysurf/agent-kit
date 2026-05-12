from __future__ import annotations

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
