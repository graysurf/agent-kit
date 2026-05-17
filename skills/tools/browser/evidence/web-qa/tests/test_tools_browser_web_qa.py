from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return " ".join(text.split())


def test_tools_browser_web_qa_contract() -> None:
    assert_skill_contract(_skill_root())


def test_tools_browser_web_qa_has_no_placeholder_scripts() -> None:
    skill_root = _skill_root()

    assert not (skill_root / "scripts").exists()
    assert "Do not add skill-local scripts or placeholder scripts" in _skill_text()


def test_tools_browser_web_qa_documents_static_evidence_mode() -> None:
    text = _skill_text()

    expected = [
        "web-evidence capture <url> --out \"$run_dir/web-evidence\"",
        "summary.json",
        "headers.redacted.json",
        "body-preview.redacted.txt",
        "--browser static-web-evidence",
        "browser-session verify --out \"$run_dir/browser-session\" --format json",
    ]

    for item in expected:
        assert item in text


def test_tools_browser_web_qa_documents_active_browser_evidence_path() -> None:
    text = _skill_text()
    compact = _compact(text)

    for browser in ["Browser", "Chrome", "Playwright", "nils-cli browser driver"]:
        assert browser in text

    expected = [
        "Active mode must perform real browser work before recording success.",
        "browser-session init",
        "--browser <Browser|Chrome|Playwright|nils-cli-driver>",
        "browser-session record-step",
        "--artifact <artifact-path>",
        "browser-session verify --out \"$session_dir\" --format json",
    ]

    for item in expected:
        assert item in text

    assert "a screenshot, DOM observation, console summary, or network summary artifact" in compact


def test_tools_browser_web_qa_documents_static_insufficiency_and_chrome_use() -> None:
    text = _skill_text()
    compact = _compact(text)

    assert "Static evidence is insufficient for JavaScript-rendered UI" in compact
    assert "Use active browser mode when the claim depends on a real browser" in text
    assert "use the user's Chrome profile when the task needs existing cookies" in text
    assert "Do not export cookies or profile state" in text


def test_tools_browser_web_qa_documents_redaction_and_blocked_states() -> None:
    text = _skill_text()
    compact = _compact(text)

    for guardrail in [
        "Do not retain raw cookies, credentials, auth headers",
        "secret query parameters and fragments",
        "Do not commit run directories unless the project explicitly defines",
        "MFA, CAPTCHA, payment, destructive action, or access-control bypass",
        "record the blocked step as `fail`",
        "`browser-session verify`",
    ]:
        assert guardrail in compact
