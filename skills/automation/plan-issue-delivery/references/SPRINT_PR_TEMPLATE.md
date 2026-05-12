# Sprint PR Template (plan-issue lanes)

This template is the canonical PR-body shape for sprint PRs opened by
plan-issue implementation lanes (`PLAN_BRANCH` base, sprint-scoped
heads). It is intentionally **separate** from the GitHub feature PR
template at
`skills/workflows/pr/github/create-github-pr/references/FEATURE_PR_TEMPLATE.md`,
which uses the `Summary / Changes / Testing / Risk / Notes` shape.

The validator in
`$AGENT_HOME/skills/workflows/issue/issue-pr-review/scripts/manage_issue_pr_review.sh`
enforces this shape via `validate_pr_body_hygiene_text` and reports
`schema: sprint-pr (Summary / Scope / Testing / Issue)` plus the path
to this file when a sprint PR body fails hygiene. Operators who hit
that error must either rewrite the PR body to match this template or,
if the PR is a non-sprint feature/bug PR by mistake, switch to the
appropriate `create-github-pr` feature/bug template instead.

> TODO (sprint 4): the legacy claude-kit wrapper at
> `plugins/plan-issue/skills/plan-issue-delivery/SKILL.md` is updated to
> point at this template in claude-kit Sprint 4 Task 4.2 — see the plan
> at `docs/plans/plan-issue-delivery-improvements-plan.md` (Sprint 4) in
> graysurf/claude-kit. Until that lands, the wrapper still defers to
> the canonical contract here.

## Required schema

A sprint PR body MUST include the following four `## H2` sections, in
order, each with at least one non-placeholder bullet. The validator
also rejects placeholder strings (`<...>`, `TODO`, `TBD`, `#<number>`,
`not run (reason)`, `<command> (pass)`).

```markdown
## Summary

- One-line description of the sprint scope this PR delivers.
- Optional second bullet for cross-cutting concerns or follow-ups.

## Scope

- Concrete list of files / modules touched, mapped to plan task IDs
  when relevant (e.g. `S1T1`, `S2T3`).
- Keep the granularity at file or feature level — not per-line.

## Testing

- `<command>` (pass) — replace with the actual command and outcome.
- Reference at least one validation command run locally or in CI.

## Issue

- #<ISSUE_NUMBER>
```

## Notes

- The `## Issue` section MUST contain the literal bullet `- #<n>`
  where `<n>` is the plan-issue number. The validator runs
  `grep -E '^[[:space:]]*-[[:space:]]*#<n>([^0-9]|$)'` against the body
  when an issue number is provided.
- If a sprint PR groups multiple tasks (PR grouping intent
  `group` / `per-sprint`), list each task ID in `## Scope` so reviewers
  can map the diff back to the plan.
- Use canonical `#<number>` PR / issue refs everywhere; never raw URLs
  inside the four required sections.
- For PRs that intentionally skip a validation command (rare),
  document the skip with a real explanation under `## Testing` rather
  than `not run (reason)` placeholder text — the validator rejects
  that exact placeholder.

## Anti-patterns

- Do **not** use the feature PR sections (`## Changes`, `## Risk / Notes`)
  on a plan-issue sprint PR. Switch templates if you opened the wrong
  type of PR.
- Do **not** leave `<...>` placeholders in the body; fill or delete the
  bullet.
- Do **not** drop the `## Issue` bullet pointing at the plan issue —
  the issue is the runtime-truth source for sprint linkage.
