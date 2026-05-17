from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def test_tools_devex_docs_impact_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_devex_docs_impact_documents_command_surface() -> None:
    text = _skill_text()

    expected = [
        "docs-impact scan [--repo <dir>] [--base <ref>] [--include-untracked] [--format json]",
        "docs-impact completion <bash|zsh>",
    ]

    for command in expected:
        assert command in text


def test_tools_devex_docs_impact_documents_artifacts_and_schema() -> None:
    text = _skill_text()

    expected = [
        "cli.docs-impact.scan.v1",
        "docs_files",
        "non_docs_files",
        "docs_changed",
        "non_docs_changed",
        "suggested_review",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_docs_impact_documents_release_and_fallback_boundaries() -> None:
    text = _skill_text()

    expected = [
        "`nils-cli 0.8.4` or newer",
        "release that includes",
        "`nils-agent-workflow-primitives`",
        "validated local `nils-cli` checkout",
        "version older than `0.8.4`",
        "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml",
        "-p nils-agent-workflow-primitives --bin docs-impact --",
        "Do not mix PATH and local checkout evidence claims",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_docs_impact_documents_guardrails() -> None:
    text = _skill_text()

    expected = [
        "Do not treat `docs-impact` output as proof that docs are complete",
        "Do not let this CLI edit docs",
        "Do not reimplement Git diff classification",
    ]

    for needle in expected:
        assert needle in text
