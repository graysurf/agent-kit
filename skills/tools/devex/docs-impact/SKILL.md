---
name: docs-impact
description: Scan Git changes for documentation impact through the nils-cli docs-impact command.
---

# Docs Impact

Use this skill when implementation or release work needs a deterministic check for changed docs and likely stale documentation.

## Contract

Prereqs:

- Run inside or point at a Git worktree.
- Released usage: `docs-impact` available on `PATH` from the `nils-cli` release that includes `nils-agent-workflow-primitives`.
- Pre-release local usage: Rust/Cargo plus a validated local `nils-cli` checkout that builds `nils-agent-workflow-primitives`.

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

## Commands

Released PATH command:

```bash
docs-impact scan [--repo <dir>] [--base <ref>] [--include-untracked] [--format json]
docs-impact completion <bash|zsh>
```

Pre-release local checkout command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin docs-impact -- scan --format json
```

Treat this as a drift detector. A clean result does not prove docs are perfect; it only means the changed-file heuristic found no obvious
docs-impact signal.
