from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def test_tools_devex_review_evidence_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_devex_review_evidence_documents_command_surface() -> None:
    text = _skill_text()

    expected = [
        "review-evidence init --out <dir> --subject <subject>",
        "review-evidence record-finding --out <dir> --severity high|medium|low",
        "review-evidence record-validation --out <dir> --command <command> --status pass|fail",
        "review-evidence verify --out <dir>",
        "review-evidence show --out <dir>",
        "review-evidence completion <bash|zsh>",
    ]

    for command in expected:
        assert command in text


def test_tools_devex_review_evidence_documents_artifacts_and_schema() -> None:
    text = _skill_text()

    expected = [
        "review-evidence.json",
        "cli.review-evidence.verify.v1",
        "requires at least one finding",
        "no open high/medium findings",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_review_evidence_documents_release_and_fallback_boundaries() -> None:
    text = _skill_text()

    expected = [
        "`nils-cli 0.8.4` or newer",
        "release that includes",
        "`nils-agent-workflow-primitives`",
        "validated local `nils-cli` checkout",
        "version older than `0.8.4`",
        "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml",
        "-p nils-agent-workflow-primitives --bin review-evidence --",
        "Do not mix PATH and local checkout evidence claims",
    ]

    for needle in expected:
        assert needle in text


def test_tools_devex_review_evidence_documents_guardrails() -> None:
    text = _skill_text()

    expected = [
        "Keep code-review judgment in the workflow",
        "Do not use `review-evidence` as a substitute for code-review judgment",
        "Do not mark high or medium findings fixed without corresponding validation evidence",
        "Do not hand-edit `review-evidence.json`",
    ]

    for needle in expected:
        assert needle in text
