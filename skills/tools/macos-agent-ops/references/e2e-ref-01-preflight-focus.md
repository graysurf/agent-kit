# Reference 01: Preflight + Input Source + Focus Check

Goal: mirror the intent of `crates/macos-agent/tests/e2e_real_macos.rs`.

## Source test reference

- `crates/macos-agent/tests/e2e_real_macos.rs`

## Quick usage

```bash
# Resolve debug binary path
$AGENT_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh where

# Ensure deterministic input source (im-select path)
$AGENT_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh input-source --id abc

# Readiness with probes + AX smoke
$AGENT_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh doctor

# Validate Finder can become foreground app (includes --reopen-on-fail)
$AGENT_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh app-check --app Finder

# AX tree probe against Arc (or another target app)
$AGENT_HOME/skills/tools/macos-agent-ops/scripts/macos-agent-ops.sh ax-check --app Arc --role AXWindow
```

## What this catches

- TCC permission issues (Accessibility/Automation).
- input-source misconfiguration that breaks keyboard typing.
- Foreground activation drift before running longer flows.
- AX tree probe failures before running long browser scenarios.
