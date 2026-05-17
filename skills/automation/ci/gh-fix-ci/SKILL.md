---
name: gh-fix-ci
description:
  "Fully automated GitHub Actions CI fixer: inspect failing checks, apply fixes, semantic-commit-autostage + push, then watch CI and repeat
  until green."
---

# GitHub CI Auto Fix

## Contract

Prereqs:

- Run inside the target git repo (or pass `--repo`).
- `git`, `gh`, and `python3` available on `PATH`.
- `semantic-commit` and `git-scope` available on `PATH` (required for commits).
- Evidence primitives available on `PATH` for unattended fix loops:
  `test-first-evidence`, `agent-scope-lock`, `canary-check`, and `web-evidence`.
- `gh auth status` succeeds for the repo (workflow scope required for logs).
- Push access to the target branch (PR branch or specified branch).

Inputs:

- `--repo <path>`: repo working directory (default `.`).
- `--pr <number|url>`: PR number or URL (optional).
- `--ref <branch|sha>`: branch name or commit SHA (optional).
- `--branch <name>`: branch name to inspect (alias of `--ref`).
- `--commit <sha>`: commit SHA to inspect (alias of `--ref`).
- `--limit <n>`: max workflow runs to inspect when using branch/commit targets (default `20`).
- PR-only flags: `--required` (only required checks).
- Optional log extraction flags: `--max-lines`, `--context`, `--json`.

Outputs:

- One or more fix commits pushed to the target branch.
- CI ends green (no failing required checks) or a terminal report of what blocked automation.
- Text summary or JSON report of failing checks (including log snippets when available) for each iteration.

Exit codes:

- N/A (multi-command workflow; failures surfaced from underlying commands).

Failure modes:

- Not inside a git repo or unable to resolve the PR/branch/commit target.
- `gh` missing or unauthenticated for the repo.
- `semantic-commit`/`git-scope` missing (cannot auto-commit).
- `gh pr checks` field drift; fallback fields still fail.
- `gh run list` failed for branch/commit targets.
- Logs unavailable (pending, external provider, or job log is a zip payload).
- Insufficient permissions to push to the target branch.

## Scripts (gh-fix-ci entrypoints)

- `$AGENT_HOME/skills/automation/ci/gh-fix-ci/scripts/gh-fix-ci.sh`
- `$AGENT_HOME/skills/automation/ci/gh-fix-ci/scripts/inspect_ci_checks.py`

Evidence and guardrail records are created by invoking the nils-cli primitives directly from the workflow. Do not add gh-fix-ci script
flags for evidence unless a future change needs deterministic script-owned behavior.

## TL;DR (fast paths)

```bash
$AGENT_HOME/skills/automation/ci/gh-fix-ci/scripts/gh-fix-ci.sh --pr 123
$AGENT_HOME/skills/automation/ci/gh-fix-ci/scripts/gh-fix-ci.sh --ref main
$AGENT_HOME/skills/automation/ci/gh-fix-ci/scripts/inspect_ci_checks.py --ref main --json
```

## Trigger

Use this skill when the user wants end-to-end CI fixing (no manual review pauses): diagnose, fix, commit, push, and keep iterating until CI
is green.

## Test-First Evidence Gate

- Before editing production behavior, capture failing-test evidence or an explicit waiver with `test-first-evidence`.
- This gate applies before editing production behavior.
- CI failure evidence may satisfy the failing-test evidence requirement when it includes the failing check, command/log snippet, exit status
  or failure classification, and affected test/job name.
- If the fix is docs-only, generated-only, infra-unavailable, or cannot be reproduced locally, record a waiver reason and substitute
  validation before editing production files.
- Each behavior-changing iteration starts a record before edits:

  ```bash
  test-first-evidence init --out <run-dir>/test-first \
    --classification <classification> \
    --production-path <path> \
    --format json
  ```

- Record CI failure evidence before edits when CI is the failing signal:

  ```bash
  test-first-evidence record-failing --out <run-dir>/test-first \
    --command "<ci-or-local-command>" \
    --exit-code <code> \
    --summary "<check>: <failure>" \
    --test-name "<job-or-test>" \
    --artifact <redacted-artifact> \
    --format json
  ```

- Record an explicit waiver before edits when the failure is docs-only, generated-only, infrastructure-only, external-provider-only, or not
  locally reproducible:

  ```bash
  test-first-evidence record-waiver --out <run-dir>/test-first \
    --reason "<reason>" \
    --substitute-validation "<validation>" \
    --format json
  ```

- After the fix and before `semantic-commit-autostage`, push, or final report, record and verify final validation:

  ```bash
  test-first-evidence record-final --out <run-dir>/test-first \
    --command "<validation-command>" \
    --status pass \
    --summary "<summary>" \
    --format json
  ```

  then `test-first-evidence verify --out <run-dir>/test-first --format json`.
- Each fix iteration summary must include `Change classification`, `Failing test before fix` or `Waiver reason`, `Final validation`, and
  the `test-first-evidence.json` path.

## Scope And Auxiliary Evidence Primitives

- Create or choose a project run directory for evidence, usually:
  `agent-out project --topic gh-fix-ci --mkdir`
- Scope safety:
  - Read the current lock before edits with `agent-scope-lock read --format json`.
  - If an `agent-scope-lock` is active, run `agent-scope-lock validate --changes all --format json` before staging, committing, pushing, or
    reporting completion. Stop if validation reports out-of-scope changes.
  - If gh-fix-ci creates a temporary lock for the assigned repair scope, use
    `agent-scope-lock create --path <path> --owner gh-fix-ci --note <reason> --format json`, then clear it on successful completion with
    `agent-scope-lock clear`. If the temporary lock remains, the final report must say why.
- Caller-owned local canary:
  - Use `canary-check` when one caller-owned local command is the appropriate post-fix canary:
    `canary-check run --out <run-dir>/canary --name <name> --command "<command>" --expect-exit 0 --format json`
    then `canary-check verify --out <run-dir>/canary --format json`.
  - Do not use `canary-check` to replace project-required tests, release gates, or CI watch; it records one cited local outcome.
- Static web evidence:
  - Use `web-evidence capture <url> --out <run-dir>/web-evidence --label <ci-log|deploy-preview|status-page> --format json` only for
    static URL evidence related to CI logs, deployment previews, or status pages.
  - `web-evidence` does not drive a browser, execute JavaScript, reuse cookies, or store auth headers.
- Active browser evidence:
  - Use `web-qa` active mode, backed by Browser, Chrome, or Playwright, when evidence requires browser behavior such as JavaScript,
    screenshots, console summaries, DOM interaction, authenticated browser state, or deploy preview inspection.
  - Do not persist raw cookies, credentials, auth headers, or full unredacted network logs.

## Workflow

1. Verify `gh` authentication with `gh auth status`. If unauthenticated, ask the user to run `gh auth login` (repo + workflow scopes).
2. Create a run directory for evidence and read any active scope lock:
   - `agent-out project --topic gh-fix-ci --mkdir`
   - `agent-scope-lock read --format json`
3. Resolve the target:
   - If the user provided `--pr`, use it.
   - If the user provided `--ref`/`--branch`/`--commit`, use that.
   - Otherwise attempt `gh pr view --json number,url` on the current branch; if unavailable, fall back to the current branch name (or `HEAD`
     commit when detached).
4. Inspect failing checks (GitHub Actions only):
   - For PR targets: run `inspect_ci_checks.py`, which calls `gh pr checks`.
   - For branch/commit targets: run `inspect_ci_checks.py`, which calls `gh run list` + `gh run view`.
   - For each failure, capture the check name, run URL, and log snippet.
5. Handle external providers:
   - If `detailsUrl` is not a GitHub Actions run, label as external and report the URL only.
   - For static external status URLs, optionally capture redacted evidence with `web-evidence capture`.
   - For browser-only deploy/status evidence, use `web-qa` active mode instead of `web-evidence`.
6. Auto-fix loop (repeat until green):
   - Reproduce locally when feasible (prefer the repo’s documented lint/test commands; otherwise use the failing command shown in logs).
   - Capture the Test-First Evidence Gate before production edits in each behavior-changing iteration by recording either
     `test-first-evidence record-failing` or `test-first-evidence record-waiver`.
   - Implement the minimal fix; avoid refactors.
   - Run the most relevant local validation command(s) as a gate (lint/test/build as applicable).
   - When a single caller-owned local validation command is the right canary, record it with `canary-check run` and `canary-check verify`.
   - Record final validation with `test-first-evidence record-final`, then verify with `test-first-evidence verify`.
   - If an `agent-scope-lock` is active, run `agent-scope-lock validate --changes all --format json`.
   - Commit using `semantic-commit-autostage` (single commit per iteration unless splitting is clearly beneficial).
   - Push the current branch (update the PR branch when targeting a PR).
   - Wait for CI:
     - PR: `gh pr checks <pr> --watch --interval 10 --required` (wait until required checks finish, then confirm pass/fail)
     - Branch/commit: watch the latest run for the pushed SHA (use `gh run list` then `gh run watch <run-id> --interval 10 --exit-status`)
   - If CI still fails, inspect again and continue the loop.

## Notes

- `inspect_ci_checks.py` returns exit code `1` when failures remain so it can be used in automation.
- Pending logs are reported as `log_pending`; rerun after the workflow completes.
- Guardrail: if the failure indicates missing secrets, infra outage, or an external provider, stop and report the blocking detail/URL
  instead of guessing.
- Guardrail: do not preserve raw CI logs, cookies, credentials, auth headers, or unredacted browser/network artifacts; cite redacted
  evidence records instead.
