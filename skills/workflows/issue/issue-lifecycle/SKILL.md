---
name: issue-lifecycle
description: Main-agent workflow for opening, maintaining, decomposing, and closing GitHub Issues as the single source of planning state.
---

# Issue Lifecycle

Main agent owns issue state and task decomposition; implementation is delegated to subagents via PR workflows.

## Contract

Prereqs:

- Run inside the target git repo.
- `gh` available on `PATH`, and `gh auth status` succeeds.
- `python3` available on `PATH` for decomposition rendering.

Inputs:

- Issue title/body data (or template-based body).
- Optional labels/assignees/projects/milestone metadata.
- Optional decomposition TSV spec (`task_id`, `summary`, `branch`, `worktree`, `owner`, `notes`).

Outputs:

- Issue created/updated/closed/reopened via GitHub Issues.
- Optional decomposition markdown comment posted to the issue.
- Deterministic CLI output suitable for orchestration scripts.

Exit codes:

- `0`: success
- non-zero: invalid inputs, missing tools, or `gh` command failures

Failure modes:

- Missing required subcommand flags (`--title`, `--issue`, `--spec`, etc.).
- Ambiguous body inputs (`--body` and `--body-file` together).
- Decomposition spec malformed (wrong TSV shape or empty rows).
- `gh` auth/permission failures.

## Entrypoint

- `$AGENT_HOME/skills/workflows/issue/issue-lifecycle/scripts/manage_issue_lifecycle.sh`

## Core usage

1. Create issue (main-agent owned):
   - `.../manage_issue_lifecycle.sh open --title "<title>" --use-template --label issue --label needs-triage`
2. Maintain issue body/labels while work progresses:
   - `.../manage_issue_lifecycle.sh update --issue <num> --body-file <path> --add-label in-progress`
3. Decompose work into subagent tasks:
   - `.../manage_issue_lifecycle.sh decompose --issue <num> --spec <task-split.tsv> --comment`
4. Log progress checkpoints:
   - `.../manage_issue_lifecycle.sh comment --issue <num> --body "<status update>"`
5. Close/reopen issue as workflow state changes:
   - `.../manage_issue_lifecycle.sh close --issue <num> --reason completed --comment "Implemented via #<pr>"`
   - `.../manage_issue_lifecycle.sh reopen --issue <num> --comment "Follow-up required"`

## References

- Issue body template: `references/ISSUE_BODY_TEMPLATE.md`
- Task split example spec: `references/TASK_SPLIT_SPEC.tsv`

## Notes

- Use `--dry-run` whenever composing commands from a higher-level orchestrator.
- Keep decomposition and status notes in issue comments so execution history remains traceable.
