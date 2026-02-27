# scripts

Repo-local helpers for agent-kit. Binary tools ship with `nils-cli` and are on PATH after `brew install nils-cli`; any legacy repo-local
wrappers under `commands/` should not be required for normal use.

## Structure

```text
commands/                                 Legacy repo-local wrappers (not required when using `nils-cli`).
scripts/
├── build/                                Tooling to generate bundled commands.
├── ci/                                   CI/local audit helpers.
│   └── markdownlint-audit.sh             Markdown lint audit (`markdownlint-cli2`).
├── chrome-devtools-mcp.sh                Launcher for the chrome-devtools MCP server.
├── env.zsh                               Environment defaults shared by repo scripts.
├── fix-typeset-empty-string-quotes.zsh   Normalizes `local/typeset foo=\"\"` to `foo=''`.
├── fix-zsh-typeset-initializers.zsh      Adds initializers to bare zsh `typeset/local` declarations.
├── fix-shell-style.zsh                   Runs shell style fixers (check/write).
├── lint.sh                               Runs shell + python lint/syntax checks.
├── project-resolve                       Deterministic project path resolver (bundled).
├── semgrep-scan.sh                       Runs Semgrep with local rules + curated Registry packs.
├── test.sh                               Dev test runner (repo-only).
├── check.sh                              Runs selected checks (lint/markdown/contracts/skills-layout/plans/env-bools/semgrep/tests).
└── audit-env-bools.zsh                   Audits boolean env var conventions (zsh).
```

## Bundling wrappers

Use `build/bundle-wrapper.zsh` to inline a wrapper (and its `source` files) into a single executable script. This is helpful when you want a
portable, repo-local command without external dependencies on wrapper paths.

Example (copy mode: project-resolve):

```zsh
zsh -f $AGENT_HOME/scripts/build/bundle-wrapper.zsh \
  --input "$HOME/.agents/scripts/project-resolve" \
  --output scripts/project-resolve
```

Notes:

- Only simple `source` lines and the `typeset -a sources=(...)` / `typeset -a exec_sources=(...)` patterns are supported.
- The bundler writes a shebang + minimal env exports into the output file.
- If the wrapper relies on side effects (PATH, cache dirs, etc.), you may need to expand the bundler to inline those sections too.

## Validation

### Agent-docs bootstrap helper

Use the `agent-doc-init` skill entrypoint for safe baseline initialization in new repositories:

```bash
$AGENT_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh --dry-run --project-path "$PROJECT_PATH"
$AGENT_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh --apply --project-path "$PROJECT_PATH"
```

Validate after apply:

```bash
agent-docs baseline --check --target all --strict --project-path "$PROJECT_PATH" --format text
```

### Skill contract lint

`$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh` enforces a minimal skill contract format
across `skills/**/SKILL.md`.

Requirements (inside `## Contract`, in order):

- `Prereqs:`
- `Inputs:`
- `Outputs:`
- `Exit codes:`
- `Failure modes:`

Usage:

- Validate all tracked skills: `$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh`
- Validate a specific file:
  `$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh --file skills/<path>/SKILL.md`

Exit codes:

- `0`: all validated files are compliant
- non-zero: validation/usage errors (prints `error:` lines to stderr)

### Skill layout audit

`$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/audit-skill-layout.sh` enforces a consistent tracked skill directory
layout:

- `SKILL.md` at the skill root
- Required: `tests/`
- Optional: `scripts/`, `references/`, `assets/`
- No other tracked top-level entries
- Markdown files with `TEMPLATE` in the filename must live under `references/` or `assets/templates/` within the skill

### Lint + syntax checks

`$AGENT_HOME/scripts/lint.sh` runs:

- Shell: `shellcheck` (bash) + `bash -n` + `zsh -n` (shebang-based)
- Python: `ruff` + `mypy` + `pyright`

Usage:

- Lint everything: `$AGENT_HOME/scripts/lint.sh`
- Shell only: `$AGENT_HOME/scripts/lint.sh --shell`
- Python only: `$AGENT_HOME/scripts/lint.sh --python`

### Markdown lint checks

`$AGENT_HOME/scripts/ci/markdownlint-audit.sh` runs `markdownlint-cli2` against all tracked Markdown files.

Usage:

- Strict mode (recommended): `$AGENT_HOME/scripts/ci/markdownlint-audit.sh --strict`

## Semgrep

Use `semgrep-scan.sh` to run `.semgrep.yaml` plus curated Semgrep Registry packs.

Examples:

- Default (scripting profile): `$AGENT_HOME/scripts/semgrep-scan.sh`
- Shell scripts only: `$AGENT_HOME/scripts/semgrep-scan.sh --profile shell`

## Plans

Plan tooling helps keep implementation plans concrete (executable + verifiable) and easy to split into parallel subagent tasks. Install with
`brew install nils-cli` to get `plan-tooling`, `api-*`, and `semantic-commit` on PATH.

### Plan lint

`plan-tooling validate` enforces a minimal Plan Format v1 across `docs/plans/*-plan.md`:

- Sprints: `## Sprint N: <name>`
- Tasks: `### Task N.M: <name>`
- Required per-task fields:
  - `Location` (non-empty list)
  - `Description`
  - `Dependencies` (`none` or list of `Task N.M`)
  - `Acceptance criteria` (non-empty list)
  - `Validation` (non-empty list)

Usage:

- Lint all tracked plans: `plan-tooling validate`
- Lint a specific plan: `plan-tooling validate --file docs/plans/<name>-plan.md`

### Plan scaffolding

`plan-tooling scaffold` creates a new `docs/plans/*-plan.md` file from the shared template:

- `plan-tooling scaffold --slug <kebab-case> --title "<task name>"`

### Plan JSON export

`plan-tooling to-json` parses a plan into JSON for tooling to consume:

- `plan-tooling to-json --file docs/plans/<name>-plan.md | python3 -m json.tool`

### Parallel batches

`plan-tooling batches` computes dependency layers (parallel batches) for a sprint:

- `plan-tooling batches --file docs/plans/<name>-plan.md --sprint 1 --format text`
