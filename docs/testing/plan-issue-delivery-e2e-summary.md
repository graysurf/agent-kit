# Plan-Issue-Delivery Final Execution Summary Template

Use this template after the final `ready-plan` and `close-plan` flow. Fill each field from run outputs generated during the rehearsal.

## Context

- Plan file: `docs/plans/plan-issue-delivery-e2e-test-plan.md`
- Issue number: `<issue-number>`
- Execution date window: `<start-date> -> <end-date>`
- Runtime root: `$AGENT_HOME/out/plan-issue-delivery/.../issue-<issue-number>`
- Summary owner: `<name-or-handle>`

## Issue Closure Evidence

- `close-plan` command used:
  `plan-issue close-plan --plan docs/plans/plan-issue-delivery-e2e-test-plan.md --issue <issue-number> --pr-grouping group --strategy auto --approved-comment-url <comment-url>`
- Issue URL: `<issue-url>`
- Final issue state (`OPEN`/`CLOSED`): `<state>`
- Close confirmation evidence (comment/log URL): `<evidence-url>`
- Plan-level approval URL used for close gate: `<approved-comment-url>`

## Merged PRs

| Task ID | PR | Merge Commit | Merge Evidence |
| --- | --- | --- | --- |
| S1T* | #<number> | <sha> | <url-or-log-ref> |
| S2T* | #<number> | <sha> | <url-or-log-ref> |
| S3T* | #<number> | <sha> | <url-or-log-ref> |

## Cleanup Result

- Cleanup command used:
  `scripts/check_plan_issue_worktree_cleanup.sh "$AGENT_HOME/out/plan-issue-delivery/graysurf-agent-kit/issue-<issue-number>/worktrees"`
- Cleanup status (`PASS`/`FAIL`): `<status>`
- Runtime directories checked: `<path-list>`
- Leftover worktrees (if any): `<none-or-paths>`

## Residual Risks

- Risk 1: `<risk>`
  Impact: `<impact>`
  Mitigation/owner: `<mitigation>`
- Risk 2: `<risk>`
  Impact: `<impact>`
  Mitigation/owner: `<mitigation>`
