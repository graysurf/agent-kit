# Assistant completion template (fixed)

Use this template after a successful screen-record run.

```text
Output:
- `<output video file path>`

Next prompt:
- "<a single-sentence prompt that repeats the same recording task with concrete flags/paths>"

Notes:
- Selector: <portal | active-window | window-id | app/window-name | display | display-id>
- Duration: <seconds>
- Audio: <off|system|mic|both>
- If permission failed: run `screen-record --preflight` (or `--request-permission`) and retry
```

## Prompt guidance (for reuse)

A good “next prompt” should include:

- The selector (`--portal`, `--active-window`, `--window-id`, `--app` + optional `--window-name`,
  `--display`, or `--display-id`)
- `--duration` in seconds
- `--audio` (only if non-default)
- The exact `--path` (and `.mov` vs `.mp4` expectation)

Example:

```text
Record the active window for 8 seconds with system audio to `out/screen-record/active-8s.mov`.
```
