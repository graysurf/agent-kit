from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def test_tools_devex_model_cross_check_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_devex_model_cross_check_documents_command_surface() -> None:
    text = _skill_text()

    expected = [
        "model-cross-check init --out <dir> --prompt <prompt>",
        "model-cross-check record-observation --out <dir> --role primary|checker",
        "model-cross-check verify --out <dir>",
        "model-cross-check show --out <dir>",
        "model-cross-check completion <bash|zsh>",
    ]

    for command in expected:
        assert command in text


def test_tools_devex_model_cross_check_documents_artifacts_and_schema() -> None:
    text = _skill_text()

    expected = [
        "model-cross-check.json",
        "cli.model-cross-check.verify.v1",
        "requires both primary and checker observations",
        "checker verdict is `fail`",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_model_cross_check_documents_release_and_fallback_boundaries() -> None:
    text = _skill_text()

    expected = [
        "`nils-cli 0.8.4` or newer",
        "release that includes",
        "`nils-agent-workflow-primitives`",
        "validated local `nils-cli` checkout",
        "version older than `0.8.4`",
        "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml",
        "-p nils-agent-workflow-primitives --bin model-cross-check --",
        "Do not mix PATH and local checkout evidence claims",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_model_cross_check_documents_guardrails() -> None:
    text = _skill_text()

    expected = [
        "not a model router",
        "Do not use `model-cross-check` to call providers",
        "Do not record provider credentials",
        "Do not hand-edit `model-cross-check.json`",
    ]

    for needle in expected:
        assert needle in text
