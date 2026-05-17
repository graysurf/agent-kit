from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def test_tools_devex_skill_usage_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_devex_skill_usage_documents_command_surface() -> None:
    text = _skill_text()

    expected = [
        "skill-usage init --out <dir> --skill <skill>",
        "skill-usage link-record --out <dir> --type <record-type> --path <path>",
        "skill-usage record-failure --out <dir> --phase preflight|execution|validation|cleanup|delivery",
        "skill-usage record-validation --out <dir> --command <command> --status pass|fail|skipped",
        "skill-usage record-outcome --out <dir> --status pass|fail|blocked|worked-around|accepted-risk|skipped",
        "skill-usage verify --out <dir>",
        "skill-usage show --out <dir>",
        "skill-usage completion <bash|zsh>",
    ]

    for command in expected:
        assert command in text


def test_tools_devex_skill_usage_documents_artifacts_and_schema() -> None:
    text = _skill_text()

    expected = [
        "skill-usage.record.json",
        "skill-usage.record.v1",
        "cli.skill-usage.verify.v1",
        "secret-like tokens",
        "missing final validation without waiver",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_skill_usage_documents_release_and_fallback_boundaries() -> None:
    text = _skill_text()

    expected = [
        "nils-cli 0.8.5 or newer",
        "`nils-agent-workflow-primitives`",
        "Homebrew nils-cli 0.8.5",
        "validated local `nils-cli` checkout",
        "skill-usage --version",
        "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml",
        "-p nils-agent-workflow-primitives --bin skill-usage --",
        "Do not mix PATH and local checkout evidence claims",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_skill_usage_documents_guardrails() -> None:
    text = _skill_text()

    expected = [
        "Do not hand-edit `skill-usage.record.json`",
        "Do not commit raw runtime records by default",
        "Do not use this record as a substitute for typed child evidence",
        "the CLI owns deterministic writing",
    ]

    for needle in expected:
        assert needle in text
