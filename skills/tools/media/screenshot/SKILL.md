---
name: screenshot
description: Capture a single window screenshot on macOS via screen-record.
---

# Screenshot

Capture a single window screenshot on macOS using the `screen-record` CLI.

## Contract

Prereqs:

- `screen-record` available on `PATH` (install via `brew install nils-cli`).
- macOS 12+ for real screenshots (uses ScreenCaptureKit).
- Screen Recording permission granted (use `screen-record --preflight` / `--request-permission`).
- `bash` for `scripts/screenshot.sh`.

Inputs:

- `scripts/screenshot.sh` is a thin wrapper around `screen-record`.
- Mode selection:
  - Default: screenshot mode (wrapper adds `--screenshot` unless a different mode flag is present).
  - Discovery: `--list-windows` / `--list-apps`.
  - Permissions: `--preflight` / `--request-permission`.
- Screenshot selectors (choose one):
  - `--window-id <id>`, or
  - `--active-window`, or
  - `--app <name>` (optional `--window-name <name>` with `--app`).
- Screenshot output args:
  - `--path <file>` (recommended), or
  - `--dir <dir>` (used when `--path` is omitted), plus optional `--image-format png|jpg|webp`.

Outputs:

- Screenshot success: stdout prints only the resolved output image path (one line).
- List success: stdout prints only UTF-8 TSV rows (no header), one per line.
- Preflight/request success: stdout is empty; any user messaging goes to stderr.
- Errors: stdout is empty; stderr contains user-facing errors (no stack traces).

Exit codes:

- `0`: success
- `1`: runtime failure or missing dependency
- `2`: usage error (invalid flags/ambiguous selection/unsupported platform)

Failure modes:

- `screen-record` missing on `PATH`.
- Non-macOS runtime (without `CODEX_SCREEN_RECORD_TEST_MODE`) returns a usage error.
- Screen Recording permission missing/denied.
- Ambiguous `--app` / `--window-name` selection (no single match).
- Invalid flag combinations.

## Scripts (only entrypoints)

- `$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh`

## Usage

- Screenshot (active window) to `$CODEX_HOME/out/` (recommended):

```bash
$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh --active-window --path "$CODEX_HOME/out/screenshot.png"
```

- List windows to find a `--window-id`:

```bash
$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh --list-windows
```

- Screenshot by app/window title:

```bash
$CODEX_HOME/skills/tools/media/screenshot/scripts/screenshot.sh --app "Terminal" --window-name "Docs" --path "$CODEX_HOME/out/terminal-docs.png"
```

- Permission preflight / request (if blocked):

```bash
screen-record --preflight
screen-record --request-permission
```

## Notes

- Prefer writing under `"$CODEX_HOME/out/"` so outputs are easy to attach/inspect.
