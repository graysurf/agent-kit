from __future__ import annotations

from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_workflows_issue_issue_follow_up_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_issue_follow_up_is_entrypoint_not_replacement() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    assert "routing layer" in text
    assert "Use `issue-lifecycle` for open, update, comment, close, and reopen operations." in text
    assert "Use normal implementation and PR workflows" in text


def test_issue_follow_up_documents_open_and_follow_up_modes() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    assert "### Open Mode" in text
    assert "### Follow-Up Mode" in text
    assert "### Implementation Handoff" in text
    assert "## Follow-up YYYY-MM-DD" in text
    assert "comment-only | blocked | ready-for-implementation | implemented-via-pr | close" in text


def test_issue_follow_up_documents_static_http_evidence_boundary() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    assert "## Static HTTP evidence" in text
    assert "public or internal HTTP/HTTPS URL" in text
    assert "web-evidence capture <url>" in text
    assert "redacted artifacts" in text
    assert "summary.json" in text
    assert "headers.redacted.json" in text
    assert "body-preview.redacted.txt" in text
    assert "JavaScript behavior" in text
    assert "authenticated/cookie-backed state" in text
