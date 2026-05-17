---
name: review-evidence
description: Record review findings and final validation through the nils-cli review-evidence command.
---

# Review Evidence

Use this skill when review findings need a normalized, mergeable evidence record before delivery or follow-up handoff.

## Contract

Prereqs:

- Keep code-review judgment in the workflow; use this CLI only for structured evidence capture.
- Choose an explicit output directory, preferably under a project-scoped `agent-out` run directory.
- Required released PATH usage: `review-evidence` available on `PATH` from `nils-cli 0.8.4` or newer.
- Release boundary: `0.8.4` is the release that includes `nils-agent-workflow-primitives`.
- Local checkout fallback: Rust/Cargo plus a validated local `nils-cli` checkout that builds `nils-agent-workflow-primitives`, used
  only when the PATH binary is absent or reports a version older than `0.8.4`.

Inputs:

- `init`: required `--out DIR` and `--subject TEXT`; optional `--reviewer TEXT`, `--force`, and `--format text|json`.
- `record-finding`: required `--out DIR`, `--severity high|medium|low`, `--path PATH`, and `--summary TEXT`; optional `--line N`,
  `--status open|fixed|accepted-risk`, repeatable `--artifact PATH`, and `--format text|json`.
- `record-validation`: required `--out DIR`, `--command TEXT`, and `--status pass|fail`; optional `--summary TEXT` and
  `--format text|json`.
- `verify` / `show`: required `--out DIR`; optional `--format text|json`.

Outputs:

- Writes `review-evidence.json` under `--out DIR`.
- JSON stdout uses versioned schema values such as `cli.review-evidence.verify.v1`.
- `verify` requires at least one finding, passing validation, and no open high/medium findings.

Exit codes:

- `0`: command succeeded; for `verify`, review evidence is complete.
- `1`: runtime failure or incomplete review evidence.
- `64`: usage error.

Failure modes:

- `review-evidence` is unavailable on `PATH` and no validated local checkout invocation is being used.
- Evidence directory cannot be created or written.
- `verify` finds no findings, missing or failing validation, or open high/medium findings.
- Caller uses this record as a substitute for reviewing the patch; judgment remains in the workflow.

## Setup

Required released PATH boundary:

```bash
review-evidence --version
```

Use the PATH command when it resolves to `nils-cli 0.8.4` or newer.

Local checkout fallback boundary:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin review-evidence -- --version
```

Run the Cargo form from the workflow's target directory. It is only a fallback transport for a validated local checkout when the released
PATH binary is absent or too old. Do not mix PATH and local checkout evidence claims without stating which source was used.

## Commands

Required released PATH command:

```bash
review-evidence init --out <dir> --subject <subject> [--format json]
review-evidence record-finding --out <dir> --severity high|medium|low --path <path> --summary <summary> [--status fixed]
review-evidence record-validation --out <dir> --command <command> --status pass|fail [--format json]
review-evidence verify --out <dir> [--format json]
review-evidence show --out <dir> [--format json]
review-evidence completion <bash|zsh>
```

Local checkout fallback command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin review-evidence -- <subcommand> ...
```

## Guardrails

- Do not use `review-evidence` as a substitute for code-review judgment or patch inspection.
- Do not mark high or medium findings fixed without corresponding validation evidence.
- Do not hand-edit `review-evidence.json` or duplicate finding, validation, schema, or JSON envelope logic in skill-local scripts.
