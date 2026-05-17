---
name: create-plan
description:
  Create a comprehensive, phased implementation plan and save it under docs/plans/. Use when the user asks for an implementation plan (make
  a plan, outline the steps, break down tasks, etc.). Do not use as the primary artifact when the user only needs a durable review finding,
  improvement backlog, or handoff record; route that to review-to-improvement-doc or handoff-session-prompt as appropriate.
---

# Create Plan

Create detailed, phased implementation plans (sprints + atomic tasks) for bugs, features, or refactors. This skill produces a plan document
only; it does not implement.

## Contract

Prereqs:

- User is asking for an implementation plan (not asking you to build it yet).
- You can read enough repo context to plan safely (or the user provides constraints).
- `plan-tooling` available on `PATH` for linting/parsing/splitting (`validate`, `to-json`, `batches`, `split-prs`; install via
  `brew install nils-cli`).

Inputs:

- User request (goal, scope, constraints, success criteria).
- Optional: repo context (files, architecture notes, existing patterns).

Outputs:

- A new plan file saved to `docs/plans/<slug>-plan.md`.
- A short response that links the plan path and summarizes the approach.
- If the request is not actually an implementation plan, a short recommendation for a better durable artifact instead of forcing
  `docs/plans/`.

Exit codes:

- N/A (conversation/workflow skill)

Failure modes:

- Request remains underspecified and the user won’t confirm assumptions.
- Plan requires access/info the user cannot provide (credentials, private APIs, etc.).

## Entrypoint

- None. This is a workflow-only skill with no `scripts/` entrypoint.

## Workflow

1. Decide whether you must ask questions first

- If the request is underspecified enough to block a useful plan, ask 1-5 "need to know" questions before writing the plan.
- Follow the blocking-question structure from `$AGENT_HOME/skills/workflows/conversation/requirements-gap-scan/SKILL.md`
  (numbered questions, short options, explicit defaults).

1. Confirm that a plan is the right artifact

- Use this skill when the user needs implementation sequencing: phases, sprints, atomic tasks, validation gates, ownership boundaries, or
  PR/issue splitting.
- Do not force `docs/plans/` when the request is mainly to preserve review findings, risks, lessons learned, improvement backlog, or
  "what to fix later" guidance. Use `review-to-improvement-doc` for a project-local durable doc/runbook/backlog entry, or recommend one if
  the user did not ask you to write it.
- If the user needs both a durable review/improvement record and an execution plan, keep them distinct: preserve the stable findings in the
  project doc first, then write the plan under `docs/plans/` and link that doc under the plan's context/read-first section.
- If a durable project doc, issue, or tracker already exists, reference it rather than duplicating the full backlog inside the plan.
- If the user wants to execute or resume an existing plan or implementation-ready document, use `execute-from-implementation-doc` instead
  of creating another plan.

1. Research the repo just enough to plan well

- Identify existing patterns, modules, and similar implementations.
- Note constraints (runtime, tooling, deployment, CI, test strategy).

1. Write the plan (do not implement)

- Follow the shared baseline in `skills/workflows/plan/_shared/references/PLAN_AUTHORING_BASELINE.md`.
- Fill `Complexity` when it materially affects batching/splitting or when a task looks oversized.
- You may omit sprint scorecards unless the user explicitly wants deeper sizing analysis or execution modeling.

1. Save the plan file

- Use the shared save rules from `skills/workflows/plan/_shared/references/PLAN_AUTHORING_BASELINE.md`.

1. Lint the plan (format + executability)

- Use the shared lint flow from `skills/workflows/plan/_shared/references/PLAN_AUTHORING_BASELINE.md`.

1. Run an executability + grouping pass (mandatory)

- Use the shared executability + grouping workflow in `skills/workflows/plan/_shared/references/PLAN_AUTHORING_BASELINE.md`.
- Add sprint metadata only when the plan needs explicit grouping/parallelism metadata or the user asks for that level of execution detail.

1. Review “gotchas”

- Use the shared `Risks & gotchas` guidance from `skills/workflows/plan/_shared/references/PLAN_AUTHORING_BASELINE.md`.

## Plan Template

Shared markdown scaffold:

- `skills/workflows/plan/_shared/assets/plan-template.md`

Canonical shared authoring and validation rules:

- `skills/workflows/plan/_shared/references/PLAN_AUTHORING_BASELINE.md`

Optional scaffold helper (creates a placeholder plan; fill it before linting):

- `plan-tooling scaffold --slug <kebab-case> --title "<task name>"`
