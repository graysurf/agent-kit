from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_text() -> str:
    skill_root = Path(__file__).resolve().parents[1]
    return (skill_root / "SKILL.md").read_text(encoding="utf-8")


def test_tools_devex_agent_scope_lock_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_devex_agent_scope_lock_documents_cli_contract_surface() -> None:
    text = _skill_text()

    expected = [
        "agent-scope-lock create --path <repo-relative-path>",
        "agent-scope-lock read [--format json]",
        "agent-scope-lock validate --changes all|staged|unstaged [--format json]",
        "agent-scope-lock clear",
    ]

    for command in expected:
        assert command in text


def test_tools_devex_agent_scope_lock_documents_release_and_local_boundaries() -> None:
    text = _skill_text()

    assert "release that includes workspace version `0.8.3`" in text
    assert "validated local `nils-cli` checkout" in text
    assert "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml" in text
    assert "-p nils-agent-scope-lock --bin agent-scope-lock --" in text
    assert "Run the Cargo form from the target git work tree" in text


def test_tools_devex_agent_scope_lock_does_not_reimplement_lock_logic() -> None:
    text = _skill_text()

    assert "git rev-parse --git-path agent-scope-lock.json" in text
    assert "No skill-local lock file, parser, or artifact format" in text
    assert "Do not edit `agent-scope-lock.json` manually" in text
