---
name: docs-impact
description: Scan Git changes for documentation impact through the nils-cli docs-impact command.
---

# Docs Impact

Use this skill when implementation or release work needs a deterministic check for changed docs and likely stale documentation.

## Contract

Prereqs:

- Run inside or point at a Git worktree.
- Required released PATH usage: `docs-impact` available on `PATH` from `nils-cli 0.8.4` or newer.
- Release boundary: `0.8.4` is the release that includes `nils-agent-workflow-primitives`.
- Local checkout fallback: Rust/Cargo plus a validated local `nils-cli` checkout that builds `nils-agent-workflow-primitives`, used
  only when the PATH binary is absent or reports a version older than `0.8.4`.

Inputs:

- `scan`: optional `--repo DIR`, optional `--base REF`, optional `--include-untracked`, and optional `--format text|json`.

Outputs:

- JSON stdout uses `cli.docs-impact.scan.v1`.
- Reports `docs_files`, `non_docs_files`, `docs_changed`, `non_docs_changed`, and `suggested_review`.
- Does not edit docs; skills decide what to update.

Exit codes:

- `0`: scan succeeded.
- `1`: runtime failure, such as a missing Git worktree or Git command failure.
- `64`: usage error.

Failure modes:

- `docs-impact` is unavailable on `PATH` and no validated local checkout invocation is being used.
- `--repo` is not a Git worktree.
- `--base` is not resolvable by Git.
- Caller treats the heuristic as proof that docs are complete; it is only a drift signal.

## Setup

Required released PATH boundary:

```bash
docs-impact --version
```

Use the PATH command when it resolves to `nils-cli 0.8.4` or newer.

Local checkout fallback boundary:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin docs-impact -- --version
```

Run the Cargo form from the workflow's target directory. It is only a fallback transport for a validated local checkout when the released
PATH binary is absent or too old. Do not mix PATH and local checkout evidence claims without stating which source was used.

## Commands

Required released PATH command:

```bash
docs-impact scan [--repo <dir>] [--base <ref>] [--include-untracked] [--format json]
docs-impact completion <bash|zsh>
```

Local checkout fallback command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin docs-impact -- scan --format json
```

Treat this as a drift detector. A clean result does not prove docs are perfect; it only means the changed-file heuristic found no obvious
docs-impact signal.

## Guardrails

- Do not treat `docs-impact` output as proof that docs are complete; it is only a changed-file heuristic.
- Do not let this CLI edit docs or decide requirement coverage; the calling workflow owns those judgments.
- Do not reimplement Git diff classification, JSON schema, or output envelope logic in skill-local scripts.
