---
name: issue-subagent-pr
description: Subagent workflow for isolated worktree implementation, draft PR creation, and review-response updates linked back to the owning issue.
---

# Issue Subagent PR

Subagents implement only in dedicated worktrees, open/update PRs, and mirror key updates back to the owning issue.

## Contract

Prereqs:

- Run inside the target git repo.
- `git` and `gh` available on `PATH`, and `gh auth status` succeeds.
- Worktree branch strategy defined by the main agent.

Inputs:

- Issue number and subagent task scope.
- Branch/base/worktree naming inputs.
- PR title/body metadata and optional review-comment URL for follow-up updates.

Outputs:

- Dedicated worktree path for the task.
- Draft PR URL for the implementation branch.
- PR follow-up comments referencing main-agent review comment URLs.
- Optional mirrored issue comments for traceability.

Exit codes:

- `0`: success
- non-zero: invalid args, missing repo context, or `git`/`gh` failures

Failure modes:

- Missing required flags (`--branch`, `--issue`, `--title`, `--review-comment-url`).
- Worktree path collision.
- PR body source conflicts (`--body` and `--body-file`).
- `gh` auth/permissions insufficient to open or comment on PRs.

## Entrypoint

- `$AGENT_HOME/skills/workflows/issue/issue-subagent-pr/scripts/manage_issue_subagent_pr.sh`

## Core usage

1. Create isolated worktree:
   - `.../manage_issue_subagent_pr.sh create-worktree --branch feat/issue-123-api --base main`
2. Open draft PR and sync PR URL to issue:
   - `.../manage_issue_subagent_pr.sh open-pr --issue 123 --title "feat: api task" --use-template`
3. Respond to main-agent review comment with explicit link:
   - `.../manage_issue_subagent_pr.sh respond-review --pr 456 --review-comment-url <url> --body-file references/REVIEW_RESPONSE_TEMPLATE.md --issue 123`

## References

- PR body template: `references/PR_BODY_TEMPLATE.md`
- Review response template: `references/REVIEW_RESPONSE_TEMPLATE.md`

## Notes

- Use `--dry-run` in orchestration/testing contexts.
- Keep implementation details and evidence in PR comments; issue comments should summarize status and link back to PR artifacts.
