# Project-Dev Workflow

## Scope

- Canonical required workflow for `project-dev` context.
- Applies to repository implementation tasks: edits, tests, and delivery checks.

## Entry commands

1. `agent-docs resolve --context project-dev --strict --format checklist`
2. `agent-docs resolve --context task-tools --format checklist` (optional, when external technical lookup is needed)
3. `agent-docs baseline --check --target home --strict --format text` (only when strict resolve fails)

## Deterministic flow

1. Resolve `project-dev` in strict mode before file edits or test runs.
2. Load project-specific docs (`DEVELOPMENT.md`, repo docs) before implementation.
3. Run project-required validation commands before reporting completion.
4. Use `task-tools` lookup only as a supplement, not a replacement for project-local requirements.

## Failure handling

- `project-dev` strict resolve fails:
  - Block code edits, commits, and delivery claims.
  - Run strict baseline check and report missing docs.
  - Resume only after required docs are present.
- Project validation command fails:
  - Report failing command and key error.
  - Do not claim completion.

## Validation checklist

- [ ] `agent-docs resolve --context project-dev --strict --format checklist` exits 0 before edits.
- [ ] Required project checks are executed and results reported.
- [ ] Failures include explicit command/error details.
