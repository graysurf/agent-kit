from __future__ import annotations

import os
import subprocess
from pathlib import Path

from skills._shared.python.skill_testing import assert_entrypoints_exist, assert_skill_contract


def _repo_root() -> Path:
    if env := os.environ.get("AGENT_HOME"):
        candidate = Path(env)
        if candidate.is_dir():
            return candidate.resolve()
    return Path(__file__).resolve().parents[4]


def _script_path() -> Path:
    return _repo_root() / "skills" / "workflows" / "issue" / "issue-pr-review" / "scripts" / "manage_issue_pr_review.sh"


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(_script_path()), *args],
        cwd=str(_repo_root()),
        text=True,
        capture_output=True,
        check=False,
    )


def test_workflows_issue_issue_pr_review_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_workflows_issue_issue_pr_review_entrypoints_exist() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_entrypoints_exist(
        skill_root,
        [
            "scripts/manage_issue_pr_review.sh",
        ],
    )


def test_issue_pr_review_skill_requires_comment_link_traceability() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    assert "comment URL" in text
    assert "issue" in text.lower()


def test_issue_pr_review_skill_uses_shared_task_lane_policy() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    assert "_shared/references/TASK_LANE_CONTINUITY.md" in text


def test_issue_pr_review_skill_uses_shared_review_rubric() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    assert "_shared/references/MAIN_AGENT_REVIEW_RUBRIC.md" in text
    assert "task-fidelity" in text
    assert "correctness" in text
    assert "integration" in text
    assert "REVIEW_EVIDENCE_TEMPLATE.md" in text
    assert "--enforce-review-evidence" in text


def test_issue_pr_review_skill_uses_shared_post_review_outcomes() -> None:
    skill_md = Path(__file__).resolve().parents[1] / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    assert "_shared/references/POST_REVIEW_OUTCOMES.md" in text
    assert "row sync to" in text
    assert "retires the lane" in text
    assert "CLOSE_PR_ISSUE_SYNC_TEMPLATE.md" in text
    assert "--row-status" in text
    assert "--next-owner" in text
    assert "--close-reason" in text


def test_issue_pr_review_script_has_internal_pr_body_validator() -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "manage_issue_pr_review.sh"
    text = script_path.read_text(encoding="utf-8")
    assert "validate_pr_body_hygiene_text" in text
    assert "validate_pr_body_hygiene_input" in text
    assert "ensure_pr_body_hygiene_for_close" in text
    assert "validate_review_evidence_text" in text
    assert "validate_review_evidence_input" in text
    assert "post_review_evidence_comment" in text


def test_issue_pr_review_script_supports_structured_issue_sync_fields() -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "manage_issue_pr_review.sh"
    text = script_path.read_text(encoding="utf-8")
    assert "--issue-note-file" in text
    assert "--issue-comment-file" in text
    assert "--review-evidence" in text
    assert "--review-evidence-file" in text
    assert "--enforce-review-evidence" in text
    assert "--close-reason" in text
    assert "--next-action" in text
    assert "build_followup_issue_note" in text
    assert "build_close_issue_comment" in text


def test_issue_pr_review_script_has_no_subagent_wrapper_dependency() -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "manage_issue_pr_review.sh"
    text = script_path.read_text(encoding="utf-8")
    assert ("manage_issue_subagent_pr" + ".sh") not in text


def test_issue_pr_review_templates_include_row_state_guidance() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    issue_sync = (skill_root / "references" / "ISSUE_SYNC_TEMPLATE.md").read_text(encoding="utf-8")
    close_sync = (skill_root / "references" / "CLOSE_PR_ISSUE_SYNC_TEMPLATE.md").read_text(encoding="utf-8")
    review_evidence = (skill_root / "references" / "REVIEW_EVIDENCE_TEMPLATE.md").read_text(encoding="utf-8")
    assert "Main-agent requested updates in PR" not in issue_sync
    assert "Row status" in issue_sync
    assert "Lane action" in issue_sync
    assert "Lane state: retired" in close_sync
    assert "do not resume the closed lane" in close_sync
    assert "## Hard Gates" in review_evidence
    assert "- Scope verdict:" in review_evidence
    assert "- Correctness verdict:" in review_evidence
    assert "- Integration verdict:" in review_evidence


# -- Sprint 3 regressions ---------------------------------------------------


def _assert_no_review_evidence_post(result: subprocess.CompletedProcess[str]) -> None:
    """No `gh pr comment` side-effect (real or dry-run) and no mirrored
    `DRY-RUN-PR-COMMENT-URL` token must appear when validation fails."""
    posted = [
        line for line in result.stderr.splitlines()
        if line.startswith("dry-run: gh pr comment ")
    ]
    assert not posted, (
        f"review-evidence comment was posted before validation; stderr lines: {posted!r}"
    )
    assert "DRY-RUN-PR-COMMENT-URL" not in result.stdout, (
        f"DRY-RUN comment URL leaked to stdout despite validation failure; stdout: {result.stdout!r}"
    )
    assert "DRY-RUN-PR-COMMENT-URL" not in result.stderr, (
        f"DRY-RUN comment URL leaked to stderr despite validation failure; stderr: {result.stderr!r}"
    )


def test_merge_orders_validation_before_review_evidence_post() -> None:
    """Task 3.1: failed PR-body validation must NOT post a review-evidence
    comment. We exercise the dry-run path with a valid review-evidence
    file and an invalid PR body override, and assert that no
    `gh pr comment` call (dry-run or real) was attempted before the
    failed PR-body validation.
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--review-evidence-file",
        "tests/fixtures/issue/review_evidence_merge_valid.md",
        "--enforce-review-evidence",
        "--pr-body-file",
        "tests/fixtures/issue/pr_body_invalid_placeholder.md",
        "--dry-run",
    )
    assert result.returncode != 0, "expected non-zero exit on invalid PR body"
    assert "disallowed placeholder found" in result.stderr, result.stderr
    _assert_no_review_evidence_post(result)
    # Sanity: the script must have actually run (not crashed before validation).
    assert "merge-override" in result.stderr or "merge-current" in result.stderr or "merge-review-evidence" in result.stderr, (
        f"unexpected stderr (validator label missing): {result.stderr!r}"
    )


def test_merge_orders_review_evidence_validation_before_post() -> None:
    """Task 3.1: a failing review-evidence body must also block the comment
    post (review-evidence is validated up-front, regardless of PR-body
    override).
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--review-evidence-file",
        "tests/fixtures/issue/review_evidence_merge_with_fail_verdict.md",
        "--enforce-review-evidence",
        "--pr-body-file",
        "tests/fixtures/issue/pr_body_valid.md",
        "--dry-run",
    )
    assert result.returncode != 0
    assert "merge decision cannot include fail/blocked core verdicts" in result.stderr, result.stderr
    _assert_no_review_evidence_post(result)


def test_merge_success_still_posts_exactly_one_review_evidence_comment() -> None:
    """Task 3.1: the happy-path must still issue exactly one PR-comment
    side-effect. The script logs `dry-run: gh pr comment ...` on stderr
    once for the review-evidence post, and the dry-run URL token appears
    exactly once in the issue-side comment that mirrors it.
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--review-evidence-file",
        "tests/fixtures/issue/review_evidence_merge_valid.md",
        "--enforce-review-evidence",
        "--pr-body-file",
        "tests/fixtures/issue/pr_body_valid.md",
        "--dry-run",
    )
    assert result.returncode == 0, (
        f"expected success; rc={result.returncode}\nstderr: {result.stderr}\nstdout: {result.stdout}"
    )
    # `run_cmd` echoes `dry-run: <command>` on stderr; the review-evidence
    # post is a single `gh pr comment ...` call.
    pr_comment_lines = [
        line for line in result.stderr.splitlines()
        if line.startswith("dry-run: gh pr comment ")
    ]
    assert len(pr_comment_lines) == 1, (
        f"expected exactly one review-evidence `gh pr comment` post, got {len(pr_comment_lines)}\n"
        f"stderr: {result.stderr!r}"
    )
    # The dry-run URL token mirrors into the issue-side comment exactly once.
    occurrences = result.stderr.count("DRY-RUN-PR-COMMENT-URL")
    assert occurrences == 1, (
        f"expected the dry-run review-evidence URL to mirror into the issue once, got {occurrences} occurrences\n"
        f"stderr: {result.stderr!r}"
    )


def test_pr_body_validator_error_messages_print_line_numbers_for_placeholders() -> None:
    """Task 3.2: every regex-based rejection must print the offending line
    (or first match) with its line number.
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--pr-body-file",
        "tests/fixtures/issue/pr_body_invalid_placeholder.md",
        "--dry-run",
    )
    assert result.returncode != 0
    assert "first match at line " in result.stderr, result.stderr


def test_review_evidence_decision_mismatch_prints_line_number() -> None:
    """Task 3.2: decision-mismatch error includes the declared-decision
    line number so the operator can find and fix the specific bullet.
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--review-evidence-file",
        "tests/fixtures/issue/review_evidence_decision_mismatch.md",
        "--enforce-review-evidence",
        "--dry-run",
    )
    assert result.returncode != 0
    assert "decision mismatch" in result.stderr
    assert "declared at line " in result.stderr, result.stderr
    assert "expected line shape: - Decision: merge" in result.stderr, result.stderr


def test_review_evidence_missing_required_line_prints_example_shape() -> None:
    """Task 3.2: missing-required-line errors include an accepted-shape
    example so the operator can paste it in directly.
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--review-evidence-file",
        "tests/fixtures/issue/review_evidence_missing_required_line.md",
        "--enforce-review-evidence",
        "--dry-run",
    )
    assert result.returncode != 0
    assert "missing required evidence line" in result.stderr
    assert "expected line shape: - Correctness verdict: pass" in result.stderr, result.stderr


def test_review_evidence_missing_heading_prints_example_shape() -> None:
    """Task 3.2: missing-required-heading errors include the accepted
    `## Heading` shape.
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--review-evidence-file",
        "tests/fixtures/issue/review_evidence_missing_heading.md",
        "--enforce-review-evidence",
        "--dry-run",
    )
    assert result.returncode != 0
    assert "missing required heading '## Integration Readiness'" in result.stderr
    assert "expected line shape: ## Integration Readiness" in result.stderr, result.stderr


def test_pr_body_validator_names_sprint_pr_template_in_error() -> None:
    """Task 3.3: the validator must NAME the schema (sprint-pr) and the
    canonical template path so the operator knows which template to
    switch to (vs. claude-kit's feature-PR shape).
    """
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--pr-body-file",
        "tests/fixtures/issue/pr_body_missing_section.md",
        "--dry-run",
    )
    assert result.returncode != 0
    assert "schema: sprint-pr" in result.stderr, result.stderr
    assert (
        "skills/automation/plan-issue-delivery/references/SPRINT_PR_TEMPLATE.md"
        in result.stderr
    ), result.stderr


def test_pr_body_validator_names_template_for_missing_issue_bullet() -> None:
    """Task 3.3: missing-issue-bullet error also names SPRINT_PR_TEMPLATE.md."""
    result = _run_script(
        "merge",
        "--pr",
        "456",
        "--method",
        "merge",
        "--issue",
        "999",
        "--pr-body-file",
        "tests/fixtures/issue/pr_body_missing_issue_bullet.md",
        "--dry-run",
    )
    assert result.returncode != 0
    assert "missing required issue bullet '- #999'" in result.stderr
    assert "SPRINT_PR_TEMPLATE.md" in result.stderr, result.stderr
