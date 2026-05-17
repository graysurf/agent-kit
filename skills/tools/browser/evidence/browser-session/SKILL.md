---
name: browser-session
description: Record browser-session goals, steps, statuses, and evidence artifacts through the nils-cli browser-session command.
---

# Browser Session

Use this skill when a browser workflow needs a deterministic evidence record for target, goal, executed steps, statuses, and artifacts.

## Contract

Prereqs:

- Use Browser, Chrome, Playwright, or another browser tool to perform the actual browser operations.
- Choose an explicit output directory, preferably under a project-scoped `agent-out` run directory.
- Required released PATH usage: `browser-session` available on `PATH` from `nils-cli 0.8.4` or newer.
- Release boundary: `0.8.4` is the release that includes `nils-agent-workflow-primitives`.
- Local checkout fallback: Rust/Cargo plus a validated local `nils-cli` checkout that builds `nils-agent-workflow-primitives`, used
  only when the PATH binary is absent or reports a version older than `0.8.4`.

Inputs:

- `init`: required `--out DIR`, `--target TEXT`, and `--goal TEXT`; optional `--browser TEXT`, `--force`, and `--format text|json`.
- `record-step`: required `--out DIR`, `--action TEXT`, and `--status pass|fail`; optional `--expectation TEXT`, repeatable
  `--artifact PATH`, and `--format text|json`.
- `verify` / `show`: required `--out DIR`; optional `--format text|json`.

Outputs:

- Writes `browser-session.json` under `--out DIR`.
- JSON stdout uses versioned schema values such as `cli.browser-session.verify.v1`.
- The record schema is `browser-session.record.v1`.

Exit codes:

- `0`: command succeeded; for `verify`, session evidence is complete.
- `1`: runtime failure or incomplete session evidence.
- `64`: usage error.

Failure modes:

- `browser-session` is unavailable on `PATH` and no validated local checkout invocation is being used.
- Evidence directory cannot be created or written.
- `verify` finds no recorded steps or at least one failed step.
- Caller assumes this CLI can drive a browser; use Browser, Chrome, or Playwright for actual automation.

## Setup

Required released PATH boundary:

```bash
browser-session --version
```

Use the PATH command when it resolves to `nils-cli 0.8.4` or newer.

Local checkout fallback boundary:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin browser-session -- --version
```

Run the Cargo form from the workflow's target directory. It is only a fallback transport for a validated local checkout when the released
PATH binary is absent or too old. Do not mix PATH and local checkout evidence claims without stating which source was used.

## Commands

Required released PATH command:

```bash
browser-session init --out <dir> --target <url-or-surface> --goal <goal> [--format json]
browser-session record-step --out <dir> --action <action> --status pass|fail [--artifact <path> ...] [--format json]
browser-session verify --out <dir> [--format json]
browser-session show --out <dir> [--format json]
browser-session completion <bash|zsh>
```

Local checkout fallback command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-agent-workflow-primitives --bin browser-session -- <subcommand> ...
```

This CLI records session evidence only; it does not replace the browser automation tool that opens pages, clicks, inspects, or screenshots.

## Guardrails

- Do not treat `browser-session` as an active browser driver; use Browser, Chrome, Playwright, or another browser tool for active work.
- Do not hand-edit `browser-session.json` or duplicate schema, redaction, completeness, or JSON envelope logic in skill-local scripts.
- Do not preserve raw cookies, credentials, auth headers, URL secrets, or unredacted network logs as artifacts.
