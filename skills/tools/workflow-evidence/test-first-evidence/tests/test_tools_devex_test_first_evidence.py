from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_text() -> str:
    skill_root = Path(__file__).resolve().parents[1]
    return (skill_root / "SKILL.md").read_text(encoding="utf-8")


def test_tools_devex_test_first_evidence_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_devex_test_first_evidence_documents_cli_contract_surface() -> None:
    text = _skill_text()

    expected = [
        "test-first-evidence init --out <dir> --classification <classification>",
        "test-first-evidence record-failing --out <dir>",
        "test-first-evidence record-waiver --out <dir>",
        "test-first-evidence record-final --out <dir>",
        "test-first-evidence verify --out <dir>",
        "test-first-evidence show --out <dir>",
        "test-first-evidence completion <bash|zsh>",
    ]

    for command in expected:
        assert command in text


def test_tools_devex_test_first_evidence_documents_release_and_local_boundaries() -> None:
    text = _skill_text()

    assert "`nils-cli 0.8.4` or newer" in text
    assert "validated local `nils-cli` checkout" in text
    assert "PATH is absent" in text
    assert "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml" in text
    assert "-p nils-test-first-evidence --bin test-first-evidence --" in text


def test_tools_devex_test_first_evidence_documents_record_contract() -> None:
    text = _skill_text()

    assert "test-first-evidence.json" in text
    assert "cli.test-first-evidence.verify.v1" in text
    assert "test-first-evidence.record.v1" in text
    assert "Secret-like tokens in recorded text are redacted" in text
    assert "Do not hand-edit `test-first-evidence.json`" in text
