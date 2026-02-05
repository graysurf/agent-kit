# Screen Record guide

This skill uses the `screen-record` CLI (from `nils-cli`) to record a single window or full display
to a video file on macOS and Linux.

## Quick decision tree

- Need to pick a target window deterministically:
  - Run `screen-record --list-windows`
  - Choose a `window_id` and record with `--window-id <id>`
- Want "whatever I'm looking at right now":
  - Use `--active-window`
- Want "the Terminal window" (may be ambiguous):
  - Start with `--app Terminal`
  - If ambiguous, refine with `--window-name` or use a specific `--window-id`
- Need full desktop/non-window capture:
  - Run `screen-record --list-displays`
  - Use `--display-id <id>` (or `--display` for the main display)
- Wayland-only Linux session (no `DISPLAY`):
  - Use interactive `--portal` for recording/screenshot flows

## Preflight / permission workflow

- macOS:
  - Check status: `screen-record --preflight`
  - Best-effort request: `screen-record --request-permission`
- Linux:
  - `screen-record --preflight` validates runtime prerequisites (`ffmpeg`, X11/portal availability)
  - `screen-record --request-permission` behaves like preflight

If recording fails with a permission error on macOS, the fix is typically:

1. macOS System Settings -> Privacy & Security -> Screen Recording
2. Enable the terminal/app running the command
3. Restart the terminal/app and retry

## Mode rules (important)

- Exactly one mode must be selected:
  - `--list-windows`, `--list-apps`, `--list-displays`, `--preflight`, `--request-permission`,
    or recording (default).
- Recording mode requires:
  - exactly one selector: `--portal`, `--window-id`, `--active-window`, `--app`, `--display`,
    or `--display-id`
  - `--duration <seconds>`
  - `--path <file>`
- `--window-name` is only valid with `--app`.
- `--portal` is interactive and currently supports `--audio off` only.
- `--audio both` requires `.mov`.

## Output contract (what to parse)

- Recording success: stdout is only the resolved output file path + newline.
- List success: stdout is only TSV rows + newline (no header).
- Errors: stdout is empty; stderr contains user-facing errors.

## Examples

List windows:

```bash
screen-record --list-windows
```

List apps:

```bash
screen-record --list-apps
```

List displays:

```bash
screen-record --list-displays
```

Record the active window (no audio):

```bash
screen-record --active-window --duration 5 --audio off --path "$CODEX_HOME/out/screen-record/active-5s.mov"
```

Record the main display:

```bash
screen-record --display --duration 5 --audio off --path "$CODEX_HOME/out/screen-record/display-5s.mov"
```

Record by app name (system audio):

```bash
screen-record --app Terminal --duration 3 --audio system --path "$CODEX_HOME/out/screen-record/terminal-3s.mov"
```

If `--app` is ambiguous, pick an id and retry:

```bash
screen-record --window-id 4811 --duration 5 --audio off --path "$CODEX_HOME/out/screen-record/window-4811.mov"
```

Wayland-only Linux interactive capture:

```bash
screen-record --portal --duration 5 --audio off --path "$CODEX_HOME/out/screen-record/portal-5s.mov"
```
