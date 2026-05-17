from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def test_tools_devex_canary_check_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_devex_canary_check_documents_command_surface() -> None:
    text = _skill_text()

    expected = [
        "canary-check run --out <dir> --name <name> --command <command>",
        "canary-check verify --out <dir>",
        "canary-check show --out <dir>",
        "canary-check completion <bash|zsh>",
    ]

    for command in expected:
        assert command in text


def test_tools_devex_canary_check_documents_artifacts_and_schema() -> None:
    text = _skill_text()

    expected = [
        "canary-check.json",
        "cli.canary-check.run.v1",
        "redacted and truncated",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_canary_check_documents_release_and_fallback_boundaries() -> None:
    text = _skill_text()

    expected = [
        "`nils-cli 0.8.4` or newer",
        "release that includes",
        "`nils-agent-workflow-primitives`",
        "validated local `nils-cli` checkout",
        "version older than `0.8.4`",
        "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml",
        "-p nils-agent-workflow-primitives --bin canary-check --",
        "Do not mix PATH and local checkout evidence claims",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_canary_check_documents_guardrails() -> None:
    text = _skill_text()

    expected = [
        "caller owns command safety",
        "do not run destructive commands",
        "Do not use `canary-check` to bypass project release",
        "Do not hand-edit `canary-check.json`",
    ]

    for needle in expected:
        assert needle in text
