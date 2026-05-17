---
name: canary-check
description: Run a local canary command and persist redacted pass/fail evidence through the nils-cli canary-check command.
---

# Canary Check

Use this skill when a workflow needs a repeatable local canary result after a change, release, or deploy handoff.

## Contract

Prereqs:

- The caller owns the canary command and its side-effect profile.
- Use read-only or explicitly approved commands for release/deploy evidence.
- Released usage: `canary-check` available on `PATH` from the `nils-cli` release that includes `nils-agent-workflow-primitives`.
- Pre-release local usage: Rust/Cargo plus a validated local `nils-cli` checkout that builds `nils-agent-workflow-primitives`.

Inputs:

- `run`: required `--out DIR`, `--name TEXT`, and `--command TEXT`; optional `--expect-exit CODE`, `--preview-bytes N`, and
  `--format text|json`.
- `verify` / `show`: required `--out DIR`; optional `--format text|json`.

Outputs:

- Writes `canary-check.json` under `--out DIR`.
- JSON stdout uses versioned schema values such as `cli.canary-check.run.v1`.
- Captured stdout/stderr previews are redacted and truncated.

Exit codes:

- `0`: command succeeded; for `verify`, latest canary status is `pass`.
- `1`: runtime failure, canary command failure, or incomplete canary evidence.
- `64`: usage error.

Failure modes:

- `canary-check` is unavailable on `PATH` and no validated local checkout invocation is being used.
- Evidence directory cannot be created or written.
- The canary command cannot start or exits with a code different from `--expect-exit`.
- Caller runs a destructive canary without explicit workflow approval; the caller owns command safety.

## Commands

```bash
canary-check run --out <dir> --name <name> --command <command> [--expect-exit 0] [--format json]
canary-check verify --out <dir> [--format json]
canary-check show --out <dir> [--format json]
canary-check completion <bash|zsh>
```

Pre-release local checkout command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin canary-check -- <subcommand> ...
```

Do not use this CLI to bypass project release gates; it records one canary outcome that higher-level workflows can cite.
