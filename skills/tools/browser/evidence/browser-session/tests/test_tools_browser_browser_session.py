from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def test_tools_browser_browser_session_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_browser_browser_session_documents_command_surface() -> None:
    text = _skill_text()

    expected = [
        "browser-session init --out <dir> --target <url-or-surface> --goal <goal>",
        "browser-session record-step --out <dir> --action <action> --status pass|fail",
        "browser-session verify --out <dir>",
        "browser-session show --out <dir>",
        "browser-session completion <bash|zsh>",
    ]

    for command in expected:
        assert command in text


def test_tools_browser_browser_session_documents_artifacts_and_schema() -> None:
    text = _skill_text()

    expected = [
        "browser-session.json",
        "cli.browser-session.verify.v1",
        "browser-session.record.v1",
    ]

    for needle in expected:
        assert needle in text


def test_tools_browser_browser_session_documents_release_and_fallback_boundaries() -> None:
    text = _skill_text()

    expected = [
        "`nils-cli 0.8.4` or newer",
        "release that includes",
        "`nils-agent-workflow-primitives`",
        "validated local `nils-cli` checkout",
        "version older than `0.8.4`",
        "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml",
        "-p nils-agent-workflow-primitives --bin browser-session --",
        "Do not mix PATH and local checkout evidence claims",
    ]

    for needle in expected:
        assert needle in text


def test_tools_browser_browser_session_documents_guardrails() -> None:
    text = _skill_text()

    expected = [
        "does not replace the browser automation tool",
        "Do not treat `browser-session` as an active browser driver",
        "Do not hand-edit `browser-session.json`",
        "Do not preserve raw cookies, credentials, auth headers",
    ]

    for needle in expected:
        assert needle in text
