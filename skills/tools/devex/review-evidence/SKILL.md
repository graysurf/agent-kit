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
- Released usage: `review-evidence` available on `PATH` from the `nils-cli` release that includes `nils-agent-workflow-primitives`.
- Pre-release local usage: Rust/Cargo plus a validated local `nils-cli` checkout that builds `nils-agent-workflow-primitives`.

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

## Commands

```bash
review-evidence init --out <dir> --subject <subject> [--format json]
review-evidence record-finding --out <dir> --severity high|medium|low --path <path> --summary <summary> [--status fixed]
review-evidence record-validation --out <dir> --command <command> --status pass|fail [--format json]
review-evidence verify --out <dir> [--format json]
review-evidence show --out <dir> [--format json]
review-evidence completion <bash|zsh>
```

Pre-release local checkout command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin review-evidence -- <subcommand> ...
```
