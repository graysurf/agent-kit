---
name: gh-fix-ci
description: Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions; use `gh` to inspect checks and logs, summarize failure context, draft a fix plan, and implement only after explicit approval. Treat external providers (for example Buildkite) as out of scope and report only the details URL.
---

# GitHub PR CI Fix

## Contract

Prereqs:

- Run inside the target git repo (or pass `--repo`).
- `git`, `gh`, and `python3` available on `PATH`.
- `gh auth status` succeeds for the repo (workflow scope required for logs).

Inputs:

- `--repo <path>`: repo working directory (default `.`).
- `--pr <number|url>`: PR number or URL (optional; default current branch PR).
- Optional log extraction flags: `--max-lines`, `--context`, `--json`.

Outputs:

- Text summary or JSON report of failing PR checks, including log snippets when available.
- Non-zero exit when failing checks remain or inspection fails.

Exit codes:

- `0`: no failing checks detected.
- `1`: failing checks remain or inspection failed.
- `2`: usage error (invalid flags).

Failure modes:

- Not inside a git repo or unable to resolve the PR.
- `gh` missing or unauthenticated for the repo.
- `gh pr checks` field drift; fallback fields still fail.
- Logs unavailable (pending, external provider, or job log is a zip payload).

## Scripts (only entrypoints)

- `$CODEX_HOME/skills/workflows/pr/gh-fix-ci/scripts/gh-fix-ci.sh`
- `$CODEX_HOME/skills/workflows/pr/gh-fix-ci/scripts/inspect_pr_checks.py`

## TL;DR (fast paths)

```bash
$CODEX_HOME/skills/workflows/pr/gh-fix-ci/scripts/gh-fix-ci.sh --pr 123
$CODEX_HOME/skills/workflows/pr/gh-fix-ci/scripts/inspect_pr_checks.py --pr 123 --json
```

## Workflow

1. Verify `gh` authentication with `gh auth status`. If unauthenticated, ask the user to run `gh auth login` (repo + workflow scopes).
2. Resolve the target PR:
   - If the user provided `--pr`, use it.
   - Otherwise run `gh pr view --json number,url` on the current branch.
3. Inspect failing checks (GitHub Actions only):
   - Run `inspect_pr_checks.py` (via the wrapper or directly).
   - For each failure, capture the check name, run URL, and log snippet.
4. Handle external providers:
   - If `detailsUrl` is not a GitHub Actions run, label as external and report the URL only.
5. Summarize failures:
   - Provide a concise snippet + the run URL or note when logs are pending.
6. Draft a fix plan and ask for approval before implementation.
   - Prefer the `create-plan` skill when available.
7. After approval, implement fixes, rerun relevant tests, and re-check `gh pr checks`.

## Notes

- `inspect_pr_checks.py` returns exit code `1` when failures remain so it can be used in automation.
- Pending logs are reported as `log_pending`; rerun after the workflow completes.
