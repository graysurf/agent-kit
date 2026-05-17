---
name: web-evidence
description: Capture redacted static HTTP evidence bundles through the nils-cli web-evidence command.
---

# Web Evidence

Use this skill when an agent workflow needs deterministic, redacted evidence for one HTTP or HTTPS URL.

## Contract

Prereqs:

- `web-evidence` available on `PATH` from the `nils-cli` release that includes workspace version `0.8.3`.
- Static HTTP/HTTPS evidence only. This command does not drive a browser, execute JavaScript, reuse cookies, or use authenticated sessions.
- The caller chooses an explicit output directory, preferably under a project-scoped `agent-out` run directory.

Inputs:

- `capture`: required `URL` and `--out DIR`; optional `--format text|json`, `--label LABEL`, `--method get|head`,
  `--timeout-seconds N`, `--max-body-bytes N`, and `--body-preview-bytes N`.
- `completion`: required shell name `bash|zsh`.

Outputs:

- `web-evidence capture`: writes a redacted artifact bundle under `--out DIR`.
- `summary.json`: versioned summary with request metadata, status classification, artifact paths, redaction counts, and error metadata.
- `headers.redacted.json`: request and response header names with sensitive values redacted.
- `body-preview.redacted.txt`: truncated, redacted text body preview when the response body is text.
- JSON stdout with `--format json` uses `schema_version` value `cli.web-evidence.capture.v1`.

Exit codes:

- `0`: evidence captured and response classified as successful.
- `1`: runtime, network, or HTTP status failure; when possible, the command still writes the redacted bundle.
- `64`: usage or configuration error.

Failure modes:

- `web-evidence` is unavailable on `PATH`.
- URL is unsupported, malformed, or not HTTP/HTTPS.
- Output directory cannot be created or safely written.
- Network request fails, times out, or returns a failure HTTP status.
- Caller needs browser state, JavaScript execution, screenshots, console logs,
  cookies, or auth headers; use Browser/Chrome/Playwright tooling instead.

## Setup

Released PATH boundary:

```bash
web-evidence --help
web-evidence capture --help
```

Use the PATH command only after installing a `nils-cli` release that includes `nils-web-evidence` workspace version `0.8.3` or newer.

Pre-release local checkout boundary:

```bash
cargo run --locked --manifest-path /Users/terry/Project/sympoies/nils-cli/Cargo.toml \
  -p nils-web-evidence --bin web-evidence -- --help
```

Run the Cargo form from the workflow's target directory. It is only a transport for a validated local checkout before the released PATH
binary is available. Keep the same `web-evidence` subcommands and flags in both modes.

## Commands (only entrypoints)

Released PATH command:

```bash
web-evidence capture <url> --out <dir> [--format text|json] [--label <label>] [--method get|head]
web-evidence completion <bash|zsh>
```

Pre-release local checkout command:

```bash
cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml \
  -p nils-web-evidence --bin web-evidence -- <subcommand> ...
```

Do not reimplement HTTP fetching, redaction, schema generation, or artifact naming in skill-local scripts.

## Workflow

1. Create or choose a run directory for the current task, usually with `agent-out project --topic <topic> --mkdir`.
2. Capture static evidence:
   `web-evidence capture <url> --out <run-dir>/web-evidence --label <scenario> --format json`
3. Read `summary.json` or JSON stdout for `ok`, `status_class`, `status_code`, `artifacts`, and `error`.
4. Attach or cite only redacted artifacts from the bundle; do not preserve raw cookies, auth headers, URL secrets, or unredacted network logs.
5. If browser behavior is required, report that this static evidence command is insufficient and use a browser tool instead.

## References

- `docs/runbooks/nils-cli/skill-consumable-primitives.md`
- `docs/runbooks/nils-cli/agent-kit-skill-adoption.md`
- `docs/runbooks/skills/TOOLING_INDEX_V2.md`
