# Plan Workflows

This directory contains planning, execution, and cleanup workflows for durable implementation work.

Use these workflows when a task needs more than one conversational turn or when a repo-local artifact should be the source of truth.

## Durable Artifact Workflow

Use durable artifacts when discussion, review, planning, execution, or handoff must survive across sessions:

1. `requirements-gap-scan` when missing requirements would change scope, safety, or done criteria.
2. `discussion-to-implementation-doc` for converged requirements/design discussion that should become implementation-ready context.
3. `review-to-improvement-doc` for review findings, risks, lessons learned, or fix-later backlog.
4. `create-plan` or `create-plan-rigorous` when a durable doc needs phases, tasks, ownership lanes, or validation sequencing.
5. `execute-from-implementation-doc` when an implementation handoff, improvement record, or plan should drive long-running execution with an
   execution-state ledger.
6. `handoff-session-prompt` only when a fresh session prompt is needed; point it at the maintained source doc and execution state.
7. `durable-artifact-cleanup` after execution is complete and the coordination docs are obsolete, unreferenced, and safe to delete.

Prefer deleting obsolete coordination docs after completion and reference checks. Keep or rehome retained evidence, audit material, and
diagnostic artifacts when project policy or future validation needs require them.

## Workflow Roles

- `create-plan`: create a phased implementation plan under `docs/plans/`.
- `create-plan-rigorous`: create a higher-rigor plan with stronger sizing and execution metadata.
- `execute-from-implementation-doc`: resume implementation from an execution-ready handoff, improvement record, or plan.
- `execute-plan-parallel`: execute a markdown plan through explicitly requested parallel subagents.
- `durable-artifact-cleanup`: remove obsolete durable coordination docs after execution is complete and references are clear.
- `docs-plan-cleanup`: prune `docs/plans/` markdown with its plan-specific report format.

## Cleanup Stance

Delete stale coordination docs once they are complete, unreferenced, and no longer needed for resume. This avoids long-lived artifacts
drifting from maintained code and tests.

Do not delete retained evidence, diagnostic artifacts, raw run outputs, or compliance/audit material unless project retention rules and the
user's cleanup request explicitly allow it.
