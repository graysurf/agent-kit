# Screen Record guide

This skill uses the `screen-record` CLI (from `nils-cli`) to record a single window to a video file.

## Quick decision tree

- Need to pick a target window deterministically:
  - Run `screen-record --list-windows`
  - Choose a `window_id` and record with `--window-id <id>`
- Want “whatever I’m looking at right now”:
  - Use `--active-window`
- Want “the Terminal window” (may be ambiguous):
  - Start with `--app Terminal`
  - If ambiguous, refine with `--window-name` or use a specific `--window-id`

## Permission workflow (macOS)

- Check status: `screen-record --preflight`
- Best-effort request: `screen-record --request-permission`

If recording fails with a permission error, the fix is typically:

1. macOS System Settings → Privacy & Security → Screen Recording
2. Enable the terminal/app running the command
3. Restart the terminal/app and retry

## Mode rules (important)

- Exactly one mode must be selected:
  - `--list-windows`, `--list-apps`, `--preflight`, `--request-permission`, or recording (default).
- Recording mode requires:
  - exactly one selector: `--window-id`, `--active-window`, or `--app`
  - `--duration <seconds>`
  - `--path <file>`
- `--window-name` is only valid with `--app`.

## Output contract (what to parse)

- Recording success: stdout is only the resolved output file path + newline.
- List success: stdout is only TSV rows + newline (no header).
- Errors: stdout is empty; stderr contains user-facing errors.

## Examples

List windows:

```bash
screen-record --list-windows
```

Record the active window (no audio):

```bash
screen-record --active-window --duration 5 --audio off --path "$CODEX_HOME/out/screen-record/active-5s.mov"
```

Record by app name (system audio):

```bash
screen-record --app Terminal --duration 3 --audio system --path "$CODEX_HOME/out/screen-record/terminal-3s.mov"
```

If `--app` is ambiguous, pick an id and retry:

```bash
screen-record --window-id 4811 --duration 5 --audio off --path "$CODEX_HOME/out/screen-record/window-4811.mov"
```
