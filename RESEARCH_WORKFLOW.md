# Research Workflow

## Purpose

- Define one deterministic technical lookup flow for Codex runs.
- Keep this process outside `AGENTS.md` so it can be versioned via `AGENT_DOCS.toml`.

## Ordered flow (default)

1. Context7
   - Use Context7 first for fast, source-linked excerpts.
2. Web (via `$playwright` skill)
   - Replace generic web browsing with the Playwright skill workflow.
   - Use: `$CODEX_HOME/skills/tools/browser/playwright/scripts/playwright_cli.sh`.
   - Required precheck before proposing commands: `command -v npx >/dev/null 2>&1`.
3. GitHub via `gh`
   - Use when docs are stale, missing, or unreleased details are needed.
4. Local clone (ask first)
   - Clone only when cross-file search, run/test verification, or deep history analysis is required.
   - Ask user before cloning unless the user explicitly requested clone.

## Decision heuristics

- Need quick, traceable excerpts -> Context7.
- Need full official narrative context -> Playwright-driven web reading of official docs.
- Need latest main/unreleased behavior -> `gh` source inspection.
- Need execution-level verification -> local clone + run.

## Playwright-specific rules

- Use CLI-first Playwright skill path, not ad-hoc browser steps.
- Always snapshot before using element refs (`e*`).
- Re-snapshot after navigation or substantial UI change.
- For artifacts in this repo, write to: `out/playwright/<label>`.

## Useful commands

```bash
agent-docs resolve --context task-tools --format text
agent-docs baseline --check --target home --strict
```
