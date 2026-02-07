# Reference 03: Arc/Spotify/Finder Matrix Routine

Goal: mirror matrix-style real-app checks from `e2e_real_apps`.

## Source test reference

- `crates/macos-agent/tests/e2e_real_apps.rs`
- `crates/macos-agent/tests/real_apps/matrix.rs`
- `crates/macos-agent/tests/real_apps/cross_app.rs`

## Quick usage

```bash
# Run app readiness checks sequentially (manual matrix precheck)
$CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh app-check --app Arc --timeout-ms 15000
$CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh app-check --app Spotify --timeout-ms 15000
$CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh app-check --app Finder --timeout-ms 12000
```

## Suggested scheduled check pattern

1. Run `doctor` once.
2. Run the 3 `app-check` commands above.
3. If any command fails with `wait app-active` timeout, capture current active window screenshot:

```bash
BIN="$($CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh where)"
"$BIN" --format json observe screenshot --active-window \
  --path "$CODEX_HOME/out/macos-agent-matrix-failure.png"
```

## Common stabilization notes

- Close Control Center/Spotlight overlays before matrix runs.
- Avoid keyboard/mouse activity while checks are active.
- If Spotify launch is flaky, clear stale updater processes before rerun.
