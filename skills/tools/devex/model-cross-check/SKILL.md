---
name: model-cross-check
description: Record primary/checker model observations through the nils-cli model-cross-check command without owning provider calls.
---

# Model Cross Check

Use this skill when a workflow needs a structured record that a primary model result was cross-checked by another model or reviewer.

## Contract

Prereqs:

- Provider calls, authentication, cost controls, and prompt execution stay owned by the calling workflow or provider-specific skill.
- Choose an explicit output directory, preferably under a project-scoped `agent-out` run directory.
- Released usage: `model-cross-check` available on `PATH` from the `nils-cli` release that includes `nils-agent-workflow-primitives`.
- Pre-release local usage: Rust/Cargo plus a validated local `nils-cli` checkout that builds `nils-agent-workflow-primitives`.

Inputs:

- `init`: required `--out DIR`, `--prompt TEXT`, `--primary-model TEXT`, and `--checker-model TEXT`; optional repeatable
  `--criterion TEXT`, `--force`, and `--format text|json`.
- `record-observation`: required `--out DIR`, `--role primary|checker`, `--model TEXT`, `--verdict pass|fail|inconclusive`, and
  `--summary TEXT`; optional repeatable `--artifact PATH` and `--format text|json`.
- `verify` / `show`: required `--out DIR`; optional `--format text|json`.

Outputs:

- Writes `model-cross-check.json` under `--out DIR`.
- JSON stdout uses versioned schema values such as `cli.model-cross-check.verify.v1`.
- `verify` requires both primary and checker observations and fails if a checker verdict is `fail`.

Exit codes:

- `0`: command succeeded; for `verify`, cross-check evidence is complete.
- `1`: runtime failure or incomplete cross-check evidence.
- `64`: usage error.

Failure modes:

- `model-cross-check` is unavailable on `PATH` and no validated local checkout invocation is being used.
- Evidence directory cannot be created or written.
- `verify` finds missing primary/checker observations or a checker `fail` verdict.
- Caller assumes this CLI invokes providers; provider calls remain outside this evidence primitive.

## Commands

```bash
model-cross-check init --out <dir> --prompt <prompt> --primary-model <model> --checker-model <model> [--format json]
model-cross-check record-observation --out <dir> --role primary|checker --model <model> --verdict pass|fail|inconclusive --summary <summary>
model-cross-check verify --out <dir> [--format json]
model-cross-check show --out <dir> [--format json]
model-cross-check completion <bash|zsh>
```

Pre-release local checkout command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin model-cross-check -- <subcommand> ...
```

This is an evidence primitive, not a model router.
