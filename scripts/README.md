# scripts

Repo-local helper scripts used by local development and CI in `agent-kit`.
Use these entrypoints to keep local checks aligned with CI behavior.

## Quick start

- Full local gate (recommended before commit):
  - `scripts/check-pre-commit.sh`
- Canonical single-command gate:
  - `scripts/check.sh --all`
- Targeted runs:
  - `scripts/check.sh --docs`
  - `scripts/check.sh --entrypoint-ownership`
  - `scripts/check.sh --tests -- -m script_smoke`

## Directory layout

```text
scripts/
├── build/
│   ├── README.md
│   └── bundle-wrapper.zsh
├── ci/
│   ├── docs-freshness-audit.sh
│   ├── markdownlint-audit.sh
│   ├── stale-skill-scripts-audit.sh
│   └── third-party-artifacts-audit.sh
├── e2e/
│   ├── run_agent_docs_subagent_trials.py
│   └── summarize_agent_docs_trials.py
├── check-pre-commit.sh
├── check.sh
├── check_plan_issue_worktree_cleanup.sh
├── chrome-devtools-mcp.sh
├── clean-untracked.sh
├── env.zsh
├── fix-shell-style.zsh
├── fix-typeset-empty-string-quotes.zsh
├── fix-zsh-typeset-initializers.zsh
├── generate-third-party-artifacts.sh
├── install-homebrew-nils-cli.sh
├── lint.sh
├── project-resolve
├── semgrep-scan.sh
└── test.sh
```

## Script index

### Core validation entrypoints

- `scripts/check-pre-commit.sh`
  - Pre-commit wrapper:
    - `scripts/check.sh --all`
    - `bash scripts/ci/stale-skill-scripts-audit.sh --check`
    - `scripts/check.sh --entrypoint-ownership`
- `scripts/check.sh`
  - Main validation router for lint, docs audits, Semgrep, and pytest.
- `scripts/lint.sh`
  - Shell + Python lint/type/syntax checks.
- `scripts/test.sh`
  - Pytest runner (uses `.venv` python when available).
- `scripts/semgrep-scan.sh`
  - Semgrep scan with local rules and curated profiles.

### CI and docs/artifact audits

- `scripts/ci/markdownlint-audit.sh`
  - Markdown lint wrapper (`markdownlint-cli2`).
- `scripts/ci/third-party-artifacts-audit.sh`
  - Verifies required third-party artifacts and drift.
- `scripts/ci/docs-freshness-audit.sh`
  - Verifies required docs commands/paths are still accurate.
- `scripts/ci/stale-skill-scripts-audit.sh`
  - Classifies skill scripts as `ACTIVE` / `TRANSITIONAL` / `REMOVABLE`.
- `scripts/generate-third-party-artifacts.sh`
  - Generates `THIRD_PARTY_LICENSES.md` and `THIRD_PARTY_NOTICES.md`.

### Shell maintenance utilities

- `scripts/fix-shell-style.zsh`
  - Runs shell style auto-fixers/checkers.
- `scripts/fix-typeset-empty-string-quotes.zsh`
  - Normalizes `typeset/local foo=""` to `foo=''`.
- `scripts/fix-zsh-typeset-initializers.zsh`
  - Adds missing initializers for zsh `typeset/local` declarations.
- `scripts/audit-env-bools.zsh`
  - Audits boolean env var naming conventions.

### Workflow-specific utilities

- `scripts/check_plan_issue_worktree_cleanup.sh`
  - Checks leftover `plan-issue-delivery` worktree directories.
- `scripts/chrome-devtools-mcp.sh`
  - Launcher for chrome-devtools MCP server with repo env handling.
- `scripts/project-resolve`
  - Bundled deterministic project path resolver.

### Environment/bootstrap helpers

- `scripts/install-homebrew-nils-cli.sh`
  - CI bootstrap helper to install Homebrew + `nils-cli`.
- `scripts/clean-untracked.sh`
  - Safe-by-default git clean wrapper (`--dry-run` default, `--apply` to delete).
- `scripts/env.zsh`
  - Shared environment defaults used by repo scripts.

### E2E trial helpers

- `scripts/e2e/run_agent_docs_subagent_trials.py`
  - Runs configured agent-docs trial scenarios and captures structured results.
- `scripts/e2e/summarize_agent_docs_trials.py`
  - Converts trial JSON results into a markdown summary.

## Bundling wrappers

Use `scripts/build/bundle-wrapper.zsh` to inline a wrapper plus sourced files into a single executable.
Details and examples live in:

- `scripts/build/README.md`
