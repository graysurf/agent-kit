from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_text() -> str:
    skill_root = Path(__file__).resolve().parents[1]
    return (skill_root / "SKILL.md").read_text(encoding="utf-8")


def test_tools_browser_web_evidence_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_tools_browser_web_evidence_documents_cli_contract_surface() -> None:
    text = _skill_text()

    expected = [
        "web-evidence capture <url> --out <dir>",
        "web-evidence completion <bash|zsh>",
        "web-evidence capture <url> --out <run-dir>/web-evidence",
        "schema_version` value `cli.web-evidence.capture.v1",
    ]

    for command in expected:
        assert command in text


def test_tools_browser_web_evidence_documents_release_and_local_boundaries() -> None:
    text = _skill_text()

    assert "release that includes workspace version `0.8.3`" in text
    assert "validated local checkout" in text
    assert "cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml" in text
    assert "-p nils-web-evidence --bin web-evidence --" in text


def test_tools_browser_web_evidence_documents_redacted_artifacts() -> None:
    text = _skill_text()

    for artifact in [
        "summary.json",
        "headers.redacted.json",
        "body-preview.redacted.txt",
    ]:
        assert artifact in text

    assert "Do not reimplement HTTP fetching, redaction, schema generation, or artifact naming" in text
    assert "do not preserve raw cookies, auth headers, URL secrets, or unredacted network logs" in text


def test_tools_browser_web_evidence_keeps_browser_work_out_of_scope() -> None:
    text = _skill_text()

    assert "Static HTTP/HTTPS evidence only" in text
    assert "does not drive a browser, execute JavaScript, reuse cookies, or use authenticated sessions" in text
    assert "If browser behavior is required" in text
