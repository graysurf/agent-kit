# Reference 01: Preflight + Focus Check

Goal: mirror the intent of `crates/macos-agent/tests/e2e_real_macos.rs`.

## Source test reference

- `crates/macos-agent/tests/e2e_real_macos.rs`

## Quick usage

```bash
# Resolve debug binary path
$CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh where

# Readiness with probes
$CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh doctor

# Validate Finder can become foreground app
$CODEX_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh app-check --app Finder
```

## What this catches

- TCC permission issues (Accessibility/Automation).
- Foreground activation drift before running longer flows.
