# <feature>: <short title>

## Goal

- <target outcome>

## Acceptance Criteria

- <verifiable condition>

## Scope

- In-scope:
  - <item>
- Out-of-scope:
  - <item>

## Task Decomposition

| Task | Summary | Owner | Branch | Worktree | PR | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | <summary> | <subagent-id> | `issue/<issue-number>/t1-<slug>` | `<worktree path>` | TBD | planned | <notes> |

## Subagent PRs

- T1: TBD

## Consistency Rules

- Every `Task` in `Task Decomposition` must appear exactly once in `Subagent PRs` as `- <Task>: <PR>`.
- `Task Decomposition.PR` and `Subagent PRs` values must match for the same task.
- `Status` must be one of: `planned`, `in-progress`, `blocked`, `done`.
- `Status` = `in-progress` or `done` requires a non-`TBD` PR.
- `Owner`, `Branch`, and `Worktree` must be non-empty; `Branch` and `Worktree` must be unique across tasks.

## Risks / Uncertainties

- <risk or unknown>
- <mitigation or validation plan>

## Evidence

- <logs, test reports, screenshots, links>
