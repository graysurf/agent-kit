---
name: issue-delivery-loop
description: "Orchestrate end-to-end issue execution loops where main-agent owns issue flow/review only, subagents own implementation PRs, and close gates require approval + merged PRs."
---

# Issue Delivery Loop

## Contract

Prereqs:

- Run inside (or have access to) the target repository.
- `gh` available on `PATH`, and `gh auth status` succeeds for issue/PR reads and writes.
- Base workflow scripts exist:
  - `$AGENT_HOME/skills/workflows/issue/issue-lifecycle/scripts/manage_issue_lifecycle.sh`

Inputs:

- Main-agent issue metadata (`title`, optional body/labels/assignees/milestone).
- Optional task decomposition TSV for bootstrap comments.
- Optional review summary text.
- Approval comment URL (`https://github.com/<owner>/<repo>/(issues|pull)/<n>#issuecomment-<id>`) when closing.
- Task owners must be subagent identities (must reference `subagent`); `main-agent` ownership is invalid for implementation tasks.

Outputs:

- Deterministic orchestration over issue lifecycle commands with explicit gate checks.
- Status snapshot and review-request markdown blocks for traceable issue history.
- Issue close only when review approval and merged-PR checks pass.
- Main-agent acts as orchestrator/reviewer only; implementation branches/PRs are delegated to subagents.

Exit codes:

- `0`: success
- non-zero: usage errors, missing tools, gh failures, or gate validation failures

Failure modes:

- Missing required options (`--title`, `--issue`, `--approved-comment-url`, etc.).
- Invalid approval URL format or repo mismatch with `--repo`.
- Task rows violate close gates (status not `done`, PR missing, or PR not merged).
- Issue/PR metadata fetch fails via `gh`.
- Task `Owner` is `main-agent`/non-subagent identity in `Task Decomposition`.

## Entrypoint

- `$AGENT_HOME/skills/automation/issue-delivery-loop/scripts/manage_issue_delivery_loop.sh`

## Role Boundary (Mandatory)

- Main-agent is limited to issue orchestration:
  - open/update/snapshot/review-handoff/close gates
  - dispatch and acceptance decisions
- Main-agent must not implement issue tasks directly.
- Even for a single-PR issue, implementation must be produced by a subagent PR and then reviewed by main-agent.
- Main-agent review/merge decisions should use `issue-pr-review`; this loop skill enforces owner and close gates.

## Core usage

1. Start issue execution:
   - `.../manage_issue_delivery_loop.sh start --repo <owner/repo> --title "<title>" --label issue --task-spec <tasks.tsv>`
2. Dispatch implementation to subagent(s):
   - Use `issue-subagent-pr` workflow to create task worktrees/PRs.
3. Update status snapshot (main-agent checkpoint):
   - `.../manage_issue_delivery_loop.sh status --repo <owner/repo> --issue <number>`
4. Request review (main-agent review handoff):
   - `.../manage_issue_delivery_loop.sh ready-for-review --repo <owner/repo> --issue <number> --summary "<review focus>"`
5. Main-agent review decision:
   - Use `issue-pr-review` to request follow-up or merge after checks/review are satisfied.
6. Close after explicit review approval:
   - `.../manage_issue_delivery_loop.sh close-after-review --repo <owner/repo> --issue <number> --approved-comment-url <url>`

## Notes

- `status` and `ready-for-review` also support `--body-file` for offline/dry-run rendering in tests.
- `close-after-review` supports `--body-file` for offline gate checks; it prints `DRY-RUN-CLOSE-SKIPPED` in body-file mode.
- Use `--dry-run` to suppress write operations while previewing commands.
