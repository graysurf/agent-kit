---
name: create-plan
description:
  Create a comprehensive, phased implementation plan and save it under docs/plans/. Use when the user asks for an implementation plan (make
  a plan, outline the steps, break down tasks, etc.).
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

Exit codes:

- N/A (conversation/workflow skill)

Failure modes:

- Request remains underspecified and the user won’t confirm assumptions.
- Plan requires access/info the user cannot provide (credentials, private APIs, etc.).

## Entrypoint

- None. This is a workflow-only skill with no `scripts/` entrypoint.

## Workflow

1. Decide whether you must ask questions first

- If the request is underspecified, ask 1–5 “need to know” questions before writing the plan.
- Follow the structure from `$AGENT_HOME/skills/workflows/conversation/ask-questions-if-underspecified/SKILL.md` (numbered questions, short
  options, explicit defaults).

1. Research the repo just enough to plan well

- Identify existing patterns, modules, and similar implementations.
- Note constraints (runtime, tooling, deployment, CI, test strategy).

1. Write the plan (do not implement)

- Use sprints/phases that each produce a demoable/testable increment.
- Treat sprints as sequential integration gates; do not imply cross-sprint execution parallelism.
- Break work into atomic, independently testable tasks with explicit dependencies when execution order matters.
- Prefer within-sprint parallel lanes only when file overlap and validation scope stay manageable.
- Include file paths whenever you can be specific.
- Include a validation step per sprint (commands, checks, expected outcomes).
- Fill `Complexity` when it materially affects batching/splitting or when a task looks oversized.

1. Save the plan file

- Path: `docs/plans/<slug>-plan.md`
- Slug rules: lowercase kebab-case, 3–6 words, end with `-plan.md`.

1. Lint the plan (format + executability)

- Run: `plan-tooling validate --file docs/plans/<slug>-plan.md`
- If it fails: tighten tasks (missing fields, placeholders, unclear validations) until it passes.

1. Run an executability + grouping pass (mandatory)

- Default grouping policy for this skill:
  - If the user did not explicitly request grouping behavior, validate with metadata-first auto
    (`--strategy auto --default-pr-grouping group`).
- For each sprint, run:

  ```bash
  plan-tooling to-json --file docs/plans/<slug>-plan.md --sprint <n>
  plan-tooling batches --file docs/plans/<slug>-plan.md --sprint <n>
  plan-tooling split-prs --file docs/plans/<slug>-plan.md --scope sprint \
    --sprint <n> --strategy auto --default-pr-grouping group --format json
  ```

- If the user explicitly requests deterministic/manual grouping:
  - Provide explicit mapping for every task: `--pr-group <task-id>=<group>` (repeatable).
  - Validate with:

    ```bash
    plan-tooling split-prs --file docs/plans/<slug>-plan.md --scope sprint --sprint <n> --pr-grouping group --strategy deterministic --pr-group ... --format json
    ```

- If the user explicitly requests one shared lane per sprint:
  - Validate with:

    ```bash
    plan-tooling split-prs --file docs/plans/<slug>-plan.md --scope sprint --sprint <n> --pr-grouping per-sprint --strategy deterministic --format json
    ```

- When you add sprint metadata for grouping/parallelism, use exact case-sensitive labels:
  - `**PR grouping intent**: per-sprint|group`
  - `**Execution Profile**: serial|parallel-xN`
- Keep metadata coherent:
  - If `PR grouping intent` is `per-sprint`, do not declare parallel width `>1`.
  - If planning multi-lane parallel execution, set `PR grouping intent` to `group`.
- After each adjustment, rerun `plan-tooling validate` and the relevant `split-prs` command until the plan is stable and executable.

1. Review “gotchas”

- After saving, add/adjust a “Risks & gotchas” section: ambiguity, dependency bottlenecks, same-batch overlap hotspots, migrations, rollout,
  backwards compatibility, and rollback.

## Plan Template

Shared template (single source of truth):

- `skills/workflows/plan/_shared/assets/plan-template.md`

When a plan needs explicit grouping/parallelism metadata, extend each sprint with these exact labels:

- `**PR grouping intent**: per-sprint|group`
- `**Execution Profile**: serial|parallel-xN`

Optional scaffold helper (creates a placeholder plan; fill it before linting):

- `plan-tooling scaffold --slug <kebab-case> --title "<task name>"`
