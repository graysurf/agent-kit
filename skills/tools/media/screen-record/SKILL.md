---
name: screen-record
description: Record a single window to a video file via the screen-record CLI (macOS 12+).
---

# Screen Record

Translate a user’s natural-language request into a safe invocation of the `screen-record` CLI.

## Contract

Prereqs:

- `screen-record` available on `PATH` (install via `brew install nils-cli`).
- macOS 12+ for real recording (uses ScreenCaptureKit + AVFoundation).
- Screen Recording permission granted (use `screen-record --preflight` / `--request-permission`).

Inputs:

- Natural-language user intent (assistant translates into a command).
- Exactly one mode:
  - Discovery: `--list-windows` or `--list-apps`, or
  - Permissions: `--preflight` or `--request-permission`, or
  - Recording mode (default).
- Recording selectors (exactly one):
  - `--window-id <id>`, or
  - `--active-window`, or
  - `--app <name>` (optional `--window-name <name>` with `--app`).
- Recording args:
  - `--duration <seconds>` (required for recording)
  - `--path <file>` (required for recording)
  - optional: `--audio off|system|mic|both`, `--format mov|mp4`

Outputs:

- Recording success: stdout prints only the resolved output video path (one line).
- List success: stdout prints only UTF-8 TSV rows (no header), one per line.
- Preflight/request success: stdout is empty; any user messaging goes to stderr.
- Errors: stdout is empty; stderr contains user-facing errors (no stack traces).

Exit codes:

- `0`: success
- `1`: runtime failure
- `2`: usage error (invalid flags/ambiguous selection/invalid format)

Failure modes:

- `screen-record` missing on `PATH`.
- Non-macOS runtime (without `CODEX_SCREEN_RECORD_TEST_MODE`) returns a usage error.
- Screen Recording permission missing/denied.
- Ambiguous `--app` / `--window-name` selection (exit `2` with candidates on stderr).
- Invalid flag combinations (e.g., `--window-name` without `--app`, `--audio both` with `.mp4`,
  `--format` conflicts with `--path` extension).

## Guidance

### Preferences (optional; honor when provided)

- Selector: `--active-window` for “record what I’m looking at”; otherwise prefer `--window-id` for deterministic selection.
- Output path: prefer writing under `"$CODEX_HOME/out/screen-record/"` with a timestamped filename.
- Container: default `.mov`; use `.mp4` only when compatible with requested audio.
- Audio: default `off`; use `system`/`mic`/`both` only when explicitly requested.

### Policies (must-follow per request)

1) If underspecified: ask must-have questions first
   - Use: `skills/workflows/conversation/ask-questions-if-underspecified/SKILL.md`
   - Ask 1–5 “Need to know” questions with explicit defaults (selector, duration, audio, output path/format).
   - Do not run commands until the user answers or explicitly approves assumptions.

2) Single entrypoint (do not bypass)
   - Only run: `screen-record` (from `PATH`; install via `brew install nils-cli`).
   - Do not call other screen recording tools unless debugging `screen-record` itself.

3) Mode/flag gates (exactly one)
   - Exactly one mode: `--list-windows` / `--list-apps` / `--preflight` / `--request-permission` / recording.
   - Recording requires:
     - exactly one selector: `--window-id` / `--active-window` / `--app`
     - `--duration <seconds>` and `--path <file>`
   - `--window-name` is only valid with `--app`.
   - `--audio both` requires `.mov` (or `--format mov`).

4) Completion response (fixed)
   - After a successful run, respond using:
     - `skills/tools/media/screen-record/references/ASSISTANT_RESPONSE_TEMPLATE.md`
   - Include clickable output path(s) and a one-sentence “next prompt” that repeats the same task with concrete flags/paths.

## References

- Full guide: `skills/tools/media/screen-record/references/SCREEN_RECORD_GUIDE.md`
- Completion template: `skills/tools/media/screen-record/references/ASSISTANT_RESPONSE_TEMPLATE.md`
