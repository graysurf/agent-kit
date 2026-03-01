---
name: agent-browser
description: Automate a real browser via agent-browser CLI using the wrapper script.
---

# Agent Browser CLI

## Contract

Prereqs:

- `bash` available on `PATH`.
- `npx` available on `PATH` (provided by Node.js/npm).
- Network access on first package fetch for `agent-browser@latest`.

Inputs:

- CLI subcommand and args forwarded to the Agent Browser CLI.
- Optional env: `AGENT_BROWSER_CLI_SESSION` (injected only when `--session` is not already provided).
- Optional upstream env/config supported by `agent-browser` (for example `AGENT_BROWSER_CONFIG`, `AGENT_BROWSER_ALLOWED_DOMAINS`,
  `AGENT_BROWSER_CONTENT_BOUNDARIES`).

Outputs:

- Stdout/stderr from upstream `agent-browser`.
- Any artifacts produced by CLI commands (for example screenshot/PDF/download/state files).
- For deterministic project output, prefer explicit artifact paths under `out/agent-browser/`.

Exit codes:

- `0`: success
- `1`: wrapper runtime failure (for example, missing `npx`)
- non-zero: forwarded failure from upstream `agent-browser`

Failure modes:

- `npx` missing from `PATH`.
- Network blocked during first-time package download.
- Invalid/unsupported subcommand or flags (reported by upstream CLI).
- Browser launch/navigation failures in upstream runtime.

## Scope

- Thin wrapper only: runtime command is `npx --yes --package agent-browser@latest agent-browser ...`.
- This skill does not own website-specific automation logic or Playwright test architecture.

## Scripts (only entrypoints)

- `scripts/agent-browser.sh`

## Usage

```bash
export AGENT_HOME="${AGENT_HOME:-$HOME/.agents}"
export ABCLI="$AGENT_HOME/skills/tools/browser/agent-browser/scripts/agent-browser.sh"

"$ABCLI" --help
"$ABCLI" open https://example.com
"$ABCLI" snapshot -i
"$ABCLI" click @e1
```

## Guardrails

- Before non-help commands, verify `npx` exists: `command -v npx >/dev/null 2>&1`.
- Prefer the wrapper entrypoint instead of relying on a globally installed `agent-browser` binary.
- Run `snapshot -i` before using `@eN` refs and re-snapshot after navigation or major DOM changes.
- For screenshots/PDF/downloads/state files, write outputs under `out/agent-browser/` for traceable artifacts.
- Close sessions when done (`agent-browser close`) to avoid leaked processes.

## References

- `references/commands.md`
- `references/snapshot-refs.md`
- `references/session-management.md`
- `references/authentication.md`
- `references/video-recording.md`
- `references/profiling.md`
- `references/proxy-support.md`

## Templates

- `assets/templates/form-automation.sh`
- `assets/templates/authenticated-session.sh`
- `assets/templates/capture-workflow.sh`
