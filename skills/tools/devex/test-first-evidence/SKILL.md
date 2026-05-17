---
name: test-first-evidence
description: Record failing-test evidence, waivers, and final validation through the nils-cli test-first-evidence command.
---

# Test-First Evidence

Use this skill when an agent workflow needs a deterministic record of before-fix evidence or an explicit waiver plus final validation.

## Contract

Prereqs:

- Run inside the target project or from a directory where evidence paths make sense.
- Choose an explicit output directory, preferably under a project-scoped `agent-out` run directory.
- Released usage: `test-first-evidence` available on `PATH` from `nils-cli 0.8.4` or newer.
- Local checkout fallback usage: Rust/Cargo plus a validated local `nils-cli` checkout that builds the
  `nils-test-first-evidence` package when PATH is absent or too old.

Inputs:

- `init`: required `--out DIR` and `--classification TEXT`; optional repeatable `--production-path PATH`, repeatable `--note TEXT`,
  optional `--force`, and optional `--format text|json`.
- `record-failing`: required `--out DIR`, `--command TEXT`, `--exit-code CODE`, and `--summary TEXT`; optional `--test-name TEXT`,
  repeatable `--artifact PATH`, and optional `--format text|json`.
- `record-waiver`: required `--out DIR` and `--reason TEXT`; optional repeatable `--substitute-validation TEXT`, and optional
  `--format text|json`.
- `record-final`: required `--out DIR`, `--command TEXT`, and `--status pass|fail`; optional `--summary TEXT`, repeatable
  `--artifact PATH`, and optional `--format text|json`.
- `verify` / `show`: required `--out DIR`; optional `--format text|json`.

Outputs:

- Writes `test-first-evidence.json` under `--out DIR`.
- JSON stdout uses versioned schema values such as `cli.test-first-evidence.verify.v1`.
- The record schema is `test-first-evidence.record.v1`.
- Secret-like tokens in recorded text are redacted by the CLI.

Exit codes:

- `0`: command succeeded; for `verify`, evidence is complete.
- `1`: runtime failure or incomplete evidence.
- `64`: usage error.

Failure modes:

- `test-first-evidence` is unavailable on `PATH` and no validated local checkout invocation is being used.
- Evidence directory cannot be created or written.
- `verify` finds neither failing evidence nor waiver, missing final validation, or final validation status is not `pass`.
- Caller records unhelpful waiver text instead of a concrete reason and substitute validation; the workflow must reject weak evidence even if
  the CLI can store it.

## Setup

Released PATH boundary:

```bash
test-first-evidence --help
test-first-evidence --version
```

Use the PATH command after installing `nils-cli 0.8.4` or newer with `nils-test-first-evidence` on PATH.

Local checkout fallback boundary:

```bash
cargo run --locked --manifest-path /Users/terry/Project/sympoies/nils-cli/Cargo.toml \
  -p nils-test-first-evidence --bin test-first-evidence -- --help
```

Run the Cargo form from the workflow's target directory only when PATH is absent
or reports an older `nils-cli`. Keep the same `test-first-evidence` subcommands
and flags in both modes.

## Commands (only entrypoints)

Released PATH command:

```bash
test-first-evidence init --out <dir> --classification <classification> [--production-path <path> ...] [--format json]
test-first-evidence record-failing --out <dir> --command <command> --exit-code <code> --summary <summary> [--format json]
test-first-evidence record-waiver --out <dir> --reason <reason> [--substitute-validation <text> ...] [--format json]
test-first-evidence record-final --out <dir> --command <command> --status pass|fail [--summary <summary>] [--format json]
test-first-evidence verify --out <dir> [--format json]
test-first-evidence show --out <dir> [--format json]
test-first-evidence completion <bash|zsh>
```

Local checkout fallback command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-test-first-evidence --bin test-first-evidence -- <subcommand> ...
```

Do not hand-edit `test-first-evidence.json` or duplicate redaction, completeness, or JSON envelope logic in skill-local scripts.

## Workflow

1. Create or choose a run directory for the task:
   `agent-out project --topic <topic> --mkdir`
2. Initialize the record before production edits:
   `test-first-evidence init --out <run-dir>/test-first --classification <classification> --production-path <path> --format json`
3. Record either failing evidence or a waiver before production edits:
   `test-first-evidence record-failing ...` or `test-first-evidence record-waiver ...`
4. After implementation, record final validation:
   `test-first-evidence record-final --out <run-dir>/test-first --command <command> --status pass --format json`
5. Before reporting completion, verify:
   `test-first-evidence verify --out <run-dir>/test-first --format json`
6. Cite the generated record path and summarize only the evidence fields needed for the user.

## References

- `docs/runbooks/skills/TOOLING_INDEX_V2.md`
