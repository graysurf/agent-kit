---
name: agent-scope-lock
description: Create, read, validate, and clear edit-scope locks through the nils-cli agent-scope-lock command.
---

# Agent Scope Lock

Use this skill when an agent workflow needs a mechanical edit boundary before changing files.

## Contract

Prereqs:

- Run inside the target git work tree.
- `git` available on `PATH`.
- Released usage: `agent-scope-lock` available on `PATH` from `nils-cli 0.8.4` or newer.
- Local checkout fallback usage: Rust/Cargo plus a validated local `nils-cli` checkout that builds the
  `nils-agent-scope-lock` package when PATH is absent or too old.
- Scope paths are repository-relative paths chosen by the owning workflow or agent.

Inputs:

- `create`: one or more `--path <repo-relative-path>` flags, optional `--owner <owner>`, optional `--note <note>`, and optional
  `--format json`.
- `read`: optional `--format json`.
- `validate`: required `--changes all|staged|unstaged`, and optional `--format json`.
- `clear`: no required inputs.

Outputs:

- `agent-scope-lock create`: writes the git metadata lock file resolved by `git rev-parse --git-path agent-scope-lock.json`.
- `agent-scope-lock read`: prints the current lock state.
- `agent-scope-lock validate`: reports whether selected working-tree changes stay inside the lock scope.
- `agent-scope-lock clear`: removes the current lock file.
- No skill-local lock file, parser, or artifact format; treat the nils-cli command as the only stable contract.

Exit codes:

- `0`: command succeeded.
- non-zero: usage, git/repository, lock-state, validation, or dependency failure from `agent-scope-lock`.

Failure modes:

- `agent-scope-lock` is unavailable on `PATH` and no validated local checkout invocation is being used.
- Current directory is not inside the intended git work tree.
- Requested `create` paths are not repository-relative or do not match the intended edit boundary.
- `validate` finds changes outside the active lock scope.
- Caller mixes a local checkout fallback with a different released PATH binary; rerun with one explicit invocation source.

## Setup

Released PATH boundary:

```bash
agent-scope-lock --help
```

Use the PATH command after installing `nils-cli 0.8.4` or newer with `nils-agent-scope-lock` on PATH.

Local checkout fallback boundary:

```bash
cargo run --locked --manifest-path /Users/terry/Project/sympoies/nils-cli/Cargo.toml \
  -p nils-agent-scope-lock --bin agent-scope-lock -- --help
```

Run the Cargo form from the target git work tree, not from the nils-cli checkout.
Use it only when PATH is absent or reports an older `nils-cli`. Keep the same
`agent-scope-lock` subcommands and flags in both modes.

## Commands (only entrypoints)

Released PATH command:

```bash
agent-scope-lock create --path <repo-relative-path> [--path <path> ...] [--owner <owner>] [--note <note>] [--format json]
agent-scope-lock read [--format json]
agent-scope-lock validate --changes all|staged|unstaged [--format json]
agent-scope-lock clear
```

Local checkout fallback command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-scope-lock --bin agent-scope-lock -- <subcommand> ...
```

Do not edit `agent-scope-lock.json` manually or duplicate scope validation logic in skill scripts.

## Workflow

1. Before editing, create the narrowest practical lock:
   `agent-scope-lock create --path <path> [--path <path> ...] --owner <agent-or-workflow> --note <reason> --format json`
2. Before acting on an existing task, read the current lock:
   `agent-scope-lock read --format json`
3. Before reporting completion, staging, committing, or handing off, validate:
   `agent-scope-lock validate --changes all --format json`
4. Clear the lock only when the owning workflow has completed or explicitly hands off:
   `agent-scope-lock clear`
5. On failure, report the exact command, exit code, stdout, and stderr; do not claim the edit scope is valid.

## References

- `docs/runbooks/nils-cli/skill-consumable-primitives.md`
- `docs/runbooks/nils-cli/agent-kit-skill-adoption.md`
- `docs/runbooks/skills/TOOLING_INDEX_V2.md`
