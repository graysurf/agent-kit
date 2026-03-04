# CI Check Parity

## Purpose

`tests/test_ci_check_parity.py` enforces parity between local check entrypoints (`scripts/check.sh`) and the CI phases in `.github/workflows/lint.yml`.

The guardrail is designed to fail fast when a required `scripts/check.sh` mode is removed, renamed, or no longer invoked by lint workflow phases.

Source of truth:

- `scripts/lib/check/modes.sh` (`CHECK_MODES`)
- `scripts/lib/check/ci_phase_map.json` (phase -> `check.sh` mode mapping)
- Generated workflow blocks in `.github/workflows/lint.yml` (`# BEGIN GENERATED: check-phase-map ...`)

## Required phase mapping

Lint workflow check phases are generated from `scripts/lib/check/ci_phase_map.json`.
Do not hand-edit generated phase blocks in `.github/workflows/lint.yml`.

Regenerate phase mapping:

```bash
python3 scripts/ci/generate-lint-workflow-phases.py --write
```

Check phase mapping drift:

```bash
python3 scripts/ci/generate-lint-workflow-phases.py --check
```

## Run parity checks

```bash
scripts/check.sh --tests -- -k parity -m script_regression
```

This command is also required in lint CI (parity guard step) and is included by
`scripts/check.sh --all` because `--all` runs the full pytest suite.

## Remediation workflow

1. If a parity test fails for stale generated phase mapping, run `python3 scripts/ci/generate-lint-workflow-phases.py --write`.
2. If a check mode is renamed/added/removed, update:
   `scripts/lib/check/modes.sh` and `scripts/lib/check/ci_phase_map.json`,
   then regenerate workflow phases.
3. Re-run:

```bash
python3 scripts/ci/generate-lint-workflow-phases.py --check
scripts/check.sh --lint
scripts/check.sh --env-bools
scripts/check.sh --docs
scripts/check.sh --tests -- -k parity -m script_regression
scripts/check.sh --all
```

## Docs completion checklist (refactor follow-up)

When a refactor changes check entrypoints, CI phases, script paths, or artifact locations:

- Update affected docs in the same PR (`README.md`, `DEVELOPMENT.md`, `docs/runbooks/agent-docs/PROJECT_DEV_WORKFLOW.md`, and relevant
  `docs/testing/*.md`).
- Verify docs command/path freshness:

```bash
scripts/check.sh --docs
```

- Verify markdown quality and parity behavior:

```bash
scripts/check.sh --markdown
scripts/check.sh --tests -- -k parity -m script_regression
```
