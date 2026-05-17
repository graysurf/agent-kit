# Close-Plan Final Mile

This reference enumerates the **five close-plan artifacts** the
main-agent must produce, in production order, between the final
`accept-sprint` and the call to `plan-issue close-plan`. Treat the
list as a hard checklist: every item is a gate documented in the
canonical `## Contract` and `## Completion Policy` of
`skills/automation/issue/plan-issue-delivery/SKILL.md`. Skipping any
artifact stops the close gate.

> TODO (sprint 4): a small `plan-issue close-plan-helper` subcommand
> that automates the file writes is tracked in claude-kit Sprint 4 Task 4.2 —
> see `docs/plans/plan-issue-delivery-improvements-plan.md` (Sprint 4)
> in graysurf/claude-kit. Until that ships, this checklist is the
> source of truth for the manual sequence.

## Inputs (resolve once before starting)

- `ISSUE_NUMBER` — captured from `start-plan` output.
- `REPO_SLUG` — `owner__repo` form (canonical) used for runtime paths.
- `ISSUE_ROOT="$AGENT_HOME/out/plan-issue-delivery/<repo-slug>/issue-<ISSUE_NUMBER>"`
- `PLAN_BRANCH` — read from `$ISSUE_ROOT/plan/plan-branch.ref`.
- `DEFAULT_BRANCH` — `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`.

## Production order (numbered)

1. **`plan-conformance-review.md`** — main-agent's per-task
   conformance verdict before opening the integration PR.
   - Path: `$ISSUE_ROOT/plan/plan-conformance-review.md`
     (`PLAN_CONFORMANCE_REVIEW_PATH`).
   - Purpose: prove every plan task is satisfied by merged sprint PRs
     plus current `PLAN_BRANCH` diff.
   - Required content: per-task verdict (`pass | fail | blocked`) with
     evidence (file paths, line refs, commands), and an overall
     `Decision: merge` / `Decision: request-followup` summary.
   - Failure path: if any task fails, default action is lane
     follow-up on the original lane; main-agent corrective coding is
     an exception that must be documented in the same artifact.
   - Reference shape: see
     `out/plan-issue-test-runs/golden-*/runtime/plan/plan-conformance-review.md`.

2. **`plan-integration-pr.md`** — record of the
   `PLAN_BRANCH -> DEFAULT_BRANCH` integration PR.
   - Path: `$ISSUE_ROOT/plan/plan-integration-pr.md`
     (`PLAN_INTEGRATION_PR_PATH`).
   - Purpose: persistent traceability for the single integration PR
     main-agent owns end-to-end.
   - Required content: PR number / URL, head ref (`PLAN_BRANCH`),
     base ref (`DEFAULT_BRANCH`), title, merge method (`squash` first,
     `merge` fallback), eventually merge commit SHA + merge timestamp.
   - Production trigger: `gh pr create --base "$DEFAULT_BRANCH" --head "$PLAN_BRANCH" ...`.
   - Reference shape: see
     `out/plan-issue-test-runs/golden-*/runtime/plan/plan-integration-pr.md`.

3. **`plan-integration-ci.md`** — required-check verification for
   the integration PR.
   - Path: `$ISSUE_ROOT/plan/plan-integration-ci.md`
     (`PLAN_INTEGRATION_CI_PATH`).
   - Purpose: prove all required checks pass before merging the
     integration PR; `no checks reported` is merge-blocking unless the
     user explicitly approves an override (record the approval here).
   - Production trigger:
     `gh pr checks <integration-pr> --required --watch` followed by a
     summary table.
   - Required content: integration PR number, head/base refs, table of
     required checks with `Status` (`pass | fail`) plus URLs, and an
     explicit note when an override was used.
   - Reference shape: see
     `out/plan-issue-test-runs/golden-*/runtime/plan/plan-integration-ci.md`.

4. **Mention comment posted on the plan issue.** This is the action
   step that produces artifact 5; nothing is written to the runtime
   tree at this step yet.
   - Required action: after the integration PR is merged, post one
     plan-issue comment that mentions the merged PR via
     `gh issue comment "$ISSUE_NUMBER" --body "Final integration PR merged: #<n> (\`<PLAN_BRANCH>\` -> \`<DEFAULT_BRANCH>\`)."`.
   - Capture the comment URL returned by `gh` (or look it up via
     `gh issue view --json comments`) — that URL is the input to
     artifact 5.
   - Failure path: missing / unparseable comment URL fails the close
     gate; the issue must show the mention before `close-plan` runs.

5. **`plan-integration-mention.url`** — comment URL persisted for
   the close gate.
   - Path: `$ISSUE_ROOT/plan/plan-integration-mention.url`
     (`PLAN_INTEGRATION_MENTION_PATH`).
   - Purpose: deterministic input for `plan-issue close-plan
     --approved-comment-url <url>`; also lets restarts reuse the same
     URL without re-querying GitHub.
   - Required content: a single-line `https://github.com/<owner>/<repo>/issues/<n>#issuecomment-<id>`
     URL, no trailing whitespace beyond a single newline.
   - Production trigger:
     `printf '%s\n' "$PLAN_INTEGRATION_MENTION_URL" > "$PLAN_INTEGRATION_MENTION_PATH"`.
   - Reference shape: see
     `out/plan-issue-test-runs/golden-*/runtime/plan/plan-integration-mention.url`.

## Final call

Once all five artifacts exist and the integration PR is merged into
`DEFAULT_BRANCH`, call:

```bash
plan-issue close-plan \
  --issue "$ISSUE_NUMBER" \
  --approved-comment-url "$(cat "$ISSUE_ROOT/plan/plan-integration-mention.url")" \
  [--repo "<owner/repo>"]
```

Then sync the local default branch:

```bash
git fetch origin --prune
git switch "$DEFAULT_BRANCH" || git switch -c "$DEFAULT_BRANCH" --track "origin/$DEFAULT_BRANCH"
git pull --ff-only
```

The close gate fails if any artifact is missing, the integration PR is
not merged, the mention comment is missing, or the worktree-cleanup
gate detects leftover worktrees under `"$ISSUE_ROOT/worktrees"`.
