from __future__ import annotations

import re
from pathlib import Path

from skills._shared.python.skill_testing import assert_skill_contract


def test_automation_plan_issue_delivery_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    assert_skill_contract(skill_root)


def test_plan_issue_delivery_skill_enforces_main_agent_role_boundary() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "Main-agent is orchestration/review-only." in text
    assert "Main-agent does not implement sprint tasks directly." in text
    assert "subagent-owned PRs" in text
    assert "1 plan = 1 issue" in text
    assert "PR grouping controls" in text
    assert "PR Grouping Steps (Mandatory)" in text
    assert "group + auto" in text
    assert "group + deterministic" in text
    assert "## Full Skill Flow" in text


def test_plan_issue_delivery_skill_requires_close_for_done() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "Definition of done: execution is complete only when `close-plan` succeeds, the plan issue is closed" in text
    assert "worktree cleanup passes." in text
    assert "A successful run must terminate at `close-plan` with:" in text
    assert "If any close gate fails, treat the run as unfinished" in text


def test_plan_issue_delivery_skill_uses_binary_first_command_contract() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "plan-issue" in text
    assert "plan-issue-local" in text
    assert "start-plan" in text
    assert "start-sprint" in text
    assert "link-pr" in text
    assert "status-plan" in text
    assert "ready-sprint" in text
    assert "accept-sprint" in text
    assert "ready-plan" in text
    assert "close-plan" in text


def test_plan_issue_delivery_skill_mentions_split_prs_v2_runtime_ownership() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "split-prs" in text
    assert "grouping primitives only" in text
    assert "materializes runtime metadata" in text


def test_plan_issue_delivery_skill_defines_runtime_workspace_policy() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "$AGENT_HOME/out/plan-issue-delivery" in text
    assert "Runtime Workspace Policy (Mandatory)" in text
    assert "PLAN_SNAPSHOT_PATH" in text
    assert "SUBAGENT_INIT_SNAPSHOT_PATH" in text
    assert "DISPATCH_RECORD_PATH" in text
    assert "references/RUNTIME_LAYOUT.md" in text


def test_plan_issue_delivery_prompts_align_runtime_and_dispatch_bundle() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    repo_root = skill_root.parents[2]

    subagent_prompt = (repo_root / "prompts" / "plan-issue-delivery-subagent-init.md").read_text(encoding="utf-8")
    main_agent_prompt = (repo_root / "prompts" / "plan-issue-delivery-main-agent-init.md").read_text(encoding="utf-8")

    assert "PLAN_SNAPSHOT_PATH" in subagent_prompt
    assert "SUBAGENT_INIT_SNAPSHOT_PATH" in subagent_prompt
    assert "DISPATCH_RECORD_PATH" in subagent_prompt
    assert "$AGENT_HOME/out/plan-issue-delivery" in subagent_prompt

    assert "PLAN_SNAPSHOT_PATH" in main_agent_prompt
    assert "SUBAGENT_INIT_SNAPSHOT_PATH" in main_agent_prompt
    assert "DISPATCH_RECORD_PATH" in main_agent_prompt
    assert "$AGENT_HOME/prompts/plan-issue-delivery-subagent-init.md" in main_agent_prompt
    assert "$AGENT_HOME/out/plan-issue-delivery" in main_agent_prompt


def test_plan_issue_delivery_skill_excludes_deleted_wrapper_scripts() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert ("plan-issue-delivery" + ".sh") not in text
    assert ("manage_issue_delivery_loop" + ".sh") not in text
    assert ("manage_issue_subagent_pr" + ".sh") not in text


def test_e2e_sprint1_fixture_enforces_artifact_tokens_and_canonical_pr_markers() -> None:
    skill_root = Path(__file__).resolve().parents[1]
    repo_root = skill_root.parents[2]

    runbook_text = (repo_root / "docs" / "testing" / "plan-issue-delivery-e2e.md").read_text(encoding="utf-8")
    fixture_text = (
        repo_root / "tests" / "fixtures" / "issue" / "plan_issue_delivery_e2e_sprint1.md"
    ).read_text(encoding="utf-8")

    for token in (
        "PLAN_SNAPSHOT_PATH",
        "TASK_PROMPT_PATH",
        "SUBAGENT_INIT_SNAPSHOT_PATH",
        "DISPATCH_RECORD_PATH",
    ):
        assert token in runbook_text, f"Sprint 1 runbook is missing required artifact token: {token}"

    assert "## Task Decomposition" in fixture_text, "Sprint 1 fixture must keep the Task Decomposition section."

    task_rows = [line for line in fixture_text.splitlines() if line.startswith("| S1T")]
    assert task_rows, "Sprint 1 fixture must include task rows in the decomposition table."

    seen_pr_tokens: set[str] = set()
    for row in task_rows:
        columns = [column.strip() for column in row.split("|")[1:-1]]
        assert len(columns) >= 7, f"Malformed Sprint 1 decomposition row: {row}"
        pr_token = columns[5]
        assert re.fullmatch(r"#\d+", pr_token), (
            "Sprint 1 PR column must use canonical '#<number>' markers; "
            f"got {pr_token!r} in row: {row}"
        )
        seen_pr_tokens.add(pr_token)

    assert "#101" in seen_pr_tokens, "Sprint 1 fixture lost canonical PR marker #101."
    assert "#102" in seen_pr_tokens, "Sprint 1 fixture lost canonical PR marker #102."
