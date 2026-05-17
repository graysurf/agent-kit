---
name: web-qa
description: Run static or active web QA evidence workflows with web-evidence, Browser, Chrome, Playwright, and browser-session records.
---

# Web QA

Use this skill to choose the lightest evidence mode that can prove or disprove a browser-facing claim.

## Contract

Prereqs:

- Define the target, goal, expected behavior, and required evidence before capturing.
- Choose a project-scoped run directory, preferably from `agent-out project --topic web-qa --mkdir`.
- Use `web-evidence` for static HTTP/HTTPS captures and `browser-session` for evidence records when session traceability is useful.
- Use Browser, Chrome, Playwright, or a verified explicit nils-cli browser driver for active browser operations.
- Do not add skill-local scripts or placeholder scripts; this skill orchestrates existing browser tools and nils-cli evidence primitives.

Inputs:

- Target URL, localhost address, deployment preview, or existing browser surface.
- QA goal and acceptance criteria.
- Mode choice: `static` or `active`.
- Optional browser choice for active mode: `Browser`, `Chrome`, `Playwright`, or a future explicit nils-cli browser driver.
- Optional artifact requirements such as screenshot, DOM observation, console summary, network summary, or static response bundle.

Outputs:

- Static mode writes a redacted `web-evidence capture` bundle, including
  `summary.json`, `headers.redacted.json`, and optional
  `body-preview.redacted.txt`.
- Active mode writes or references browser evidence artifacts such as
  screenshots, DOM observations, console summaries, network summaries, or
  Playwright output files.
- When `browser-session` is used, writes `browser-session.json` with goal, target, steps, statuses, and artifact paths.
- Final response summarizes the evidence paths, pass/fail status, and any blocked state without exposing secrets.

Exit codes:

- `web-evidence capture` returns `0` for successful captures, `1` for runtime/network/HTTP failures, and `64` for usage errors.
- `browser-session verify` returns `0` when the evidence record is complete and
  all recorded steps passed, `1` when evidence is incomplete or a step failed,
  and `64` for usage errors.
- Browser, Chrome, Playwright, and future nils-cli browser-driver failures are
  tool-specific; record the step as `fail` when a session has already started.

Failure modes:

- Required browser or nils-cli evidence tool is unavailable.
- Target is inaccessible, unstable, blocked by network policy, or requires unavailable credentials.
- Static HTTP evidence is insufficient because the claim depends on JavaScript,
  DOM state, browser storage, screenshots, interaction, console logs, network
  behavior, or authenticated state.
- The requested evidence would retain raw cookies, credentials, auth headers, tokenized URLs, secret form values, or unredacted network logs.
- CAPTCHA, MFA, payment, destructive actions, or access-control bypass would be required.
- Artifact directory cannot be created or verified.

## Mode Selection

Use static evidence mode when HTTP status, redirects, headers, and a redacted
text preview are enough. Static mode is appropriate for health checks, public
preview availability, simple content checks, and status-page evidence.

Use active browser mode when the claim depends on a real browser. Static
evidence is insufficient for JavaScript-rendered UI, screenshots or layout,
responsive behavior, DOM interaction, client-side routing, console errors, local
storage/session storage, browser-only authentication, downloads, forms, viewport
checks, or console/network summaries.

Choose the active driver deliberately:

- `Browser`: use the Codex in-app Browser for local targets, unauthenticated
  pages, quick interactive open/inspect/screenshot work, and localhost QA.
- `Chrome`: use the user's Chrome profile when the task needs existing cookies,
  logged-in state, extensions, existing tabs, or another stateful/authenticated
  browser session. Do not export cookies or profile state.
- `Playwright`: use the repo Playwright wrapper when a repeatable CLI-driven
  browser path is better than interactive inspection and the target does not
  require the user's existing Chrome state.
- Explicit nils-cli browser driver: use only if a real released or validated
  local nils-cli driver exists, its command surface is verified with `--help`,
  and it actually opens or inspects a browser target. Do not invent this driver
  in the skill.

## Static Evidence Mode

Run static mode through `web-evidence capture`. If the static capture is part of a QA acceptance claim, also record it with `browser-session`.

```bash
run_dir="$(agent-out project --topic web-qa --mkdir)"
web-evidence capture <url> --out "$run_dir/web-evidence" --label <scenario> --format json

browser-session init \
  --out "$run_dir/browser-session" \
  --target <url> \
  --goal <goal> \
  --browser static-web-evidence \
  --format json

browser-session record-step \
  --out "$run_dir/browser-session" \
  --action "Captured static HTTP evidence with web-evidence" \
  --expectation <expected-behavior> \
  --status pass \
  --artifact "$run_dir/web-evidence/summary.json" \
  --artifact "$run_dir/web-evidence/headers.redacted.json" \
  --artifact "$run_dir/web-evidence/body-preview.redacted.txt" \
  --format json

browser-session verify --out "$run_dir/browser-session" --format json
```

If `web-evidence capture` exits non-zero but writes a bundle, inspect the
redacted `summary.json`, record a failed `browser-session record-step` if a
session was initialized, and report the HTTP/network failure as evidence rather
than retrying blindly.

## Active Browser Mode

Active mode must perform real browser work before recording success. Open,
inspect, interact with, or capture the target through Browser, Chrome,
Playwright, or a verified explicit nils-cli browser driver, then record the
action and artifact paths with `browser-session`.

```bash
run_dir="$(agent-out project --topic web-qa --mkdir)"
session_dir="$run_dir/browser-session"

browser-session init \
  --out "$session_dir" \
  --target <url-or-browser-surface> \
  --goal <goal> \
  --browser <Browser|Chrome|Playwright|nils-cli-driver> \
  --format json
```

Perform one or more real browser actions:

- Browser or Chrome: open or attach to the target, inspect the page, interact as
  needed, and capture a screenshot, DOM observation, console summary, or network
  summary artifact under the run directory.
- Playwright: set `PLAYWRIGHT_MCP_OUTPUT_DIR` under a project output directory,
  use `$AGENT_HOME/skills/tools/browser/playwright/scripts/playwright_cli.sh` to
  open or inspect the target, and retain the generated screenshot, snapshot,
  trace, or output file.
- nils-cli browser driver: run the explicit driver only after verifying its command surface, output location, and redaction behavior.

Then record each completed browser action:

```bash
browser-session record-step \
  --out "$session_dir" \
  --action "Opened <target> with <browser-tool> and captured <artifact-kind>" \
  --expectation <expected-behavior> \
  --status pass \
  --artifact <artifact-path> \
  --format json

browser-session verify --out "$session_dir" --format json
```

If the browser action fails after `browser-session init`, record a failed step
with the blocker and any redacted diagnostic artifact, then run
`browser-session verify` and report that verification failed because the active
browser check was blocked or failed.

## Redaction Guardrails

- Keep only redacted evidence artifacts. Do not retain raw cookies, credentials,
  auth headers, bearer tokens, session storage, local storage dumps, secret
  query strings, or unredacted network logs.
- For screenshots that reveal secrets or personal data, either avoid retaining
  the screenshot, capture a safer viewport/state, or create a redacted
  derivative before recording the artifact path.
- Summarize console and network evidence to the minimum useful facts. Preserve URLs only after removing secret query parameters and fragments.
- Do not type, reveal, or persist passwords, one-time codes, recovery codes, API keys, or customer data in evidence notes.
- Do not commit run directories unless the project explicitly defines a retained, redacted evidence path.

## Blocked States

Stop and report blocked when:

- The requested proof requires login state but Chrome is unavailable or the user
  has not approved using an existing authenticated browser session.
- MFA, CAPTCHA, payment, destructive action, or access-control bypass is required.
- The only available evidence would expose secrets and no redacted artifact can support the claim.
- Browser, Chrome, Playwright, `web-evidence`, or `browser-session` is unavailable and no scoped fallback exists.
- Static mode was requested but the requirement depends on active browser behavior.

When blocked after a session has started, record the blocked step as `fail`, run
`browser-session verify`, and include the failed verification result in the
final report.
