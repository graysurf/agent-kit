# AGENTS.md

## Purpose & scope

- This file defines the global default behavior for Codex CLI: response style, quality bar, and the minimum set of tool-entry conventions.
- Scope: when Codex CLI can't find a more specific policy file in the current working directory, it falls back to this file.
- Override rule: if the current directory (or a closer subdirectory) contains a project/folder-specific `AGENTS.md` (or equivalent), the closest one wins; otherwise fall back to this file.
- Project-specific specs, workflows, available commands/scripts, and repo structure/index should follow the current project's `README`, `docs`, `CONTRIBUTING`, `prompts`, `skills`, etc. (when present).

## Quick navigation

- How do I run/build/test this project? -> read the current project's `README`, `docs`, and `CONTRIBUTING`.
- What workflows/templates already exist? -> check the current project's `prompts/`, `skills/`, or equivalent directories (when present).
- This file only covers global response behavior and minimal tool-entry conventions; avoid duplicating or conflicting with project docs.

## Core guidelines

- Semantic and logical consistency
  - Keep meaning, terminology, and numbers consistent within a turn and across turns; avoid drift.
  - If you need to correct something, explicitly call out what changed and why (e.g., cause and before/after).

- High signal density
  - Maximize useful information per token without sacrificing accuracy or readability; avoid filler and repetition.
  - Prefer structured output (bullets, tables, quantified statements).

- Reasoning mode
  - Default to an accelerated, high-level reasoning mode; if the reasoning space gets too large, flag it and propose narrowing.

- Working with files
  - For shell scripts, code, and config: before editing/commenting, read the full context relevant to the change (definitions, call sites, loading/dependencies). It's fine to jump directly to the target area first, then backfill surrounding context as needed.
  - If information is missing or uncertain: state assumptions and what needs verification, ask for the minimum additional files/snippets, then proceed. Avoid overconfident conclusions from partial context.
  - When generating artifacts (reports/outputs/temp files):
    - Project deliverables -> write them into the project directory following that project's conventions.
    - Debug/test artifacts that would normally go to `/tmp` (e.g. `lighthouse-performance.json`) -> write to `$CODEX_HOME/out/` instead, and reference that path in the reply.

- Completion notification (desktop)
  - If you finish the user's request in a turn (e.g. implemented/fixed/delivered something), and the user didn't explicitly opt out: send one desktop notification at the end of the turn (best-effort; silent no-op on failure).
  - Message: describe what was done in <= 20 words.
  - Command (cross-platform; pass only the message): `$CODEX_HOME/skills/tools/devex/desktop-notify/scripts/project-notify.sh "Up to 20 words <**In English**>" --level info|success|warn|error`

## Response template

> Goal: make outputs scannable, verifiable, and traceable, while consistently surfacing uncertainty.

### Global response rules

- Skill-first
  - If an enabled skill (e.g. `skills/*/SKILL.md`) defines output requirements or a mandatory format (including code-block requirements), follow it.
  - If a skill conflicts with this template, the skill wins. Otherwise, keep using this template.

- Response footer
  - Every reply must end with confidence and reasoning level using this exact format:
    - `—— [Confidence: High|Medium|Low] [Reasoning: Fact|Inference|Assumption|Generated]`

- Template

  ```md
  ## Overview

  - In 2-5 lines: state the problem, the conclusion, assumptions (if any), and what you'll do next (if anything).

  ## Steps / Recommendations

  1. Actionable steps (include commands, checkpoints, and expected output when useful).
  2. If there are branches: If A -> do X; if B -> do Y.

  ## Risks / Uncertainty (when needed)

  - What is inferred vs assumed, and what missing info could change the conclusion.
  - How to validate (which file to check, which command to run, which log to read).

  ## Sources (when needed)

  - Cite filenames/paths or other traceable references.

  —— [Confidence: Medium] [Reasoning: Inference]
  ```

## Commit policy

- All commits must use `semantic-commit`
  - `$semantic-commit`: review-first, user-staged.
  - `$semantic-commit-autostage`: automation flow (allows `git add`).
- Do not run `git commit` directly.

## codex-kit

### Development (Shell / zsh)

- `stdout`/`stderr`: These scripts are designed for non-interactive use. Keep `stdout` for machine/LLM-parsable output only; send everything else (debug/progress/warn) to `stderr` (zsh: `print -u2 -r -- ...`; bash: `echo ... >&2`).
- Avoid accidental output (zsh `typeset`/`local`): don't repeatedly declare variables without initial values inside loops (e.g. `typeset key file`). With `unsetopt typeset_silent` (including the default), zsh may print existing values to `stdout` (e.g. `key=''`), creating noise.
  - Option A (preferred): declare once outside the loop -> `typeset key='' file=''`; inside the loop, only assign (`key=...`).
  - Option B: if you must declare inside the loop -> always provide an initial value (`typeset key='' file=''`).
- Quoting rules (zsh; same idea in bash)
  - Literal strings (no `$var`/`$(cmd)` expansion) -> single quotes: `typeset homebrew_path=''`
  - Needs expansion -> double quotes and keep quoting: `typeset repo_root="$PWD"`, `print -r -- "$msg"`
  - Needs escape sequences (e.g. `\n`) -> use `$'...'`
- Auto-fix (empty strings only): `scripts/fix-typeset-empty-string-quotes.zsh --check|--write` normalizes `typeset/local ...=""` to `''`.

### Testing

#### Required before committing

- Run: `scripts/check.sh --all`
- `scripts/check.sh --all` runs:
  - `scripts/lint.sh` (shell + python)
    - Shell: route by shebang and run `shellcheck` (bash) + `bash -n` + `zsh -n`
    - Python: `ruff check tests` + `mypy --config-file mypy.ini tests` + syntax-check for tracked `.py` files
  - `scripts/validate_skill_contracts.sh`
  - `scripts/semgrep-scan.sh`
  - `scripts/test.sh` (pytest; prefers `.venv/bin/python`)

#### Tooling / setup (as needed)

- Prereqs
  - Python
    - `python3 -m venv .venv`
    - `.venv/bin/pip install -r requirements-dev.txt`
  - System tools
    - `shellcheck`, `zsh` (macOS: `brew install shellcheck`; Ubuntu: `sudo apt-get install -y shellcheck zsh`)
- Quick entry points
  - `scripts/lint.sh` (defaults to shell + python)
  - `scripts/check.sh --lint` (lint only; faster iteration)
  - `scripts/check.sh --contracts` (skill-contract validation only)
  - `scripts/check.sh --tests -- -m script_smoke` (passes args through to pytest)
  - `scripts/check.sh --semgrep` (Semgrep only)
  - `scripts/check.sh --all` (full check)
- `pytest`
  - Prefer the wrapper: `scripts/test.sh` (passes args through to pytest)
  - Common: `scripts/test.sh -m script_smoke`, `scripts/test.sh -m script_regression`
  - Artifacts: written to `out/tests/` (e.g. `out/tests/script-coverage/summary.md`)
- `ruff` (Python lint; config: `ruff.toml`)
  - `source .venv/bin/activate && ruff check tests`
  - Safe autofix: `source .venv/bin/activate && ruff check --fix tests`
  - Or via: `scripts/lint.sh --python`
- `mypy` (typecheck; config: `mypy.ini`)
  - `source .venv/bin/activate && mypy --config-file mypy.ini tests`
  - Or via: `scripts/lint.sh --python`
- Shell (bash/zsh)
  - `scripts/lint.sh --shell` (requires `shellcheck` and `zsh`)
