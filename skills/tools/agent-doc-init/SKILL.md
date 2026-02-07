---
name: agent-doc-init
description: Initialize baseline agent-docs files safely for new repositories using dry-run-first workflow.
---

# Agent Doc Init

Initialize missing baseline policy documents with a non-destructive default.

## Contract

Prereqs:

- `agent-docs` available on `PATH`.
- `bash` and `python3` available on `PATH`.
- Write permission to target paths only when `--apply` is used.

Inputs:

- Entrypoint: `$CODEX_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh`.
- Optional flags:
  - `--dry-run` (default mode)
  - `--apply` (write mode)
  - `--force` (overwrite baseline docs; requires `--apply`)
  - `--target all|home|project` (default: `all`)
  - `--project-path <path>`
  - `--codex-home <path>`
  - `--project-required <context:path[:notes]>` (repeatable)

Outputs:

- Deterministic summary lines to stdout.
- Baseline checks before/after initialization.
- Optional baseline scaffolding (`scaffold-baseline --missing-only` by default).
- Optional project extension upserts via `agent-docs add`.

Exit codes:

- `0`: success (including no-op)
- `1`: runtime/dependency failure
- `2`: usage/safety contract violation

Failure modes:

- `agent-docs` is missing from `PATH`.
- Invalid `--project-required` format or unsupported context.
- `--force` is provided without `--apply`.
- `agent-docs` reports config/schema/runtime failures.
- File permission errors when writing during apply mode.

## Scripts (only entrypoints)

- `$CODEX_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh`

## Workflow

1. Run baseline check (`agent-docs baseline --check`) and capture missing counts.
2. If required docs are missing (or force mode is requested), run `scaffold-baseline`:
   - default: `--missing-only`
   - overwrite path: `--force` (only when explicitly requested)
3. Optionally upsert project extension docs via `agent-docs add` for each `--project-required`.
4. Re-run baseline check and emit deterministic summary.

## Safety defaults

- Dry-run by default (`--apply` is required for writes).
- No overwrite unless `--force` is explicitly provided.
- Missing-only scaffold is the default write behavior.
- All actions are idempotent when rerun with the same inputs.

## Usage

Preview only:

```bash
$CODEX_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh \
  --dry-run \
  --project-path /path/to/repo
```

Apply missing baseline docs:

```bash
$CODEX_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh \
  --apply \
  --project-path /path/to/repo
```

Apply and add one project extension required doc:

```bash
$CODEX_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh \
  --apply \
  --project-path /path/to/repo \
  --project-required "project-dev:BINARY_DEPENDENCIES.md:External runtime tools"
```

