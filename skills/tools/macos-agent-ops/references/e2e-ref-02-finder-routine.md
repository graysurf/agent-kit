# Reference 02: Finder Routine Flow

Goal: mirror core behavior from Finder scenario in `e2e_real_apps`.

## Source test reference

- `crates/macos-agent/tests/e2e_real_apps.rs`
- `crates/macos-agent/tests/real_apps/finder.rs`

## Quick usage

```bash
BIN="$($CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh where)"

# 1) Activate Finder and verify app-active
$CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh app-check --app Finder

# 2) New window and navigate home
"$BIN" --format json input hotkey --mods cmd --key n
"$BIN" --format json wait window-present --app Finder --timeout-ms 10000 --poll-ms 60
"$BIN" --format json input hotkey --mods cmd,shift --key h

# 3) Capture evidence
"$BIN" --format json observe screenshot --active-window \
  --path "$CODEX_HOME/out/finder-routine-active-window.png"
```

## What this catches

- Window activation failures.
- Window presence polling instability.
- Screenshot capture permission regressions.
