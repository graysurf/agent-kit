# Skills Tooling Index v2

This doc lists canonical entrypoints (skill scripts, PATH-installed tooling, and scriptless command contracts). Install `nils-cli` via
`brew install nils-cli` to get `plan-tooling`, `api-*`, `semantic-commit`, and `agent-out` on PATH; `agent-scope-lock` and `web-evidence`
require the release that includes workspace version `0.8.3`. For skill directory layout/path rules, use
`docs/runbooks/skills/SKILLS_ANATOMY_V2.md` as the canonical reference. For create/validate/remove workflows, see
`skills/tools/skill-management/README.md`.

Candidate future `nils-cli` primitives are tracked separately in
`docs/runbooks/nils-cli/skill-consumable-primitives.md`; this index lists only
implemented entrypoints.

## SKILL.md format

- SKILL.md format spec:
  - `docs/runbooks/skills/SKILL_MD_FORMAT_V1.md`
- Skill directory anatomy (canonical):
  - `docs/runbooks/skills/SKILLS_ANATOMY_V2.md`

## Skill governance

- Validate SKILL.md contract format:
  - `$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh`
- Audit tracked skill directory layout:
  - `$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/audit-skill-layout.sh`
- Validate runnable path rules in SKILL.md:
  - `$AGENT_HOME/skills/tools/skill-management/skill-governance/scripts/validate_skill_paths.sh`

## Skill management

- Create a new skill skeleton (validated):
  - `$AGENT_HOME/skills/tools/skill-management/create-skill/scripts/create_skill.sh`
- Remove a skill and purge references (breaking change):
  - `$AGENT_HOME/skills/tools/skill-management/remove-skill/scripts/remove_skill.sh`

## Plan tooling (Plan Format v1)

- Scaffold a new plan file:
  - `plan-tooling scaffold`
- Lint plans:
  - `plan-tooling validate`
- Parse plan → JSON:
  - `plan-tooling to-json`
- Compute dependency batches:
  - `plan-tooling batches`

## Issue workflow (main-agent + subagent PR automation)

- Main-agent issue lifecycle:
  - `$AGENT_HOME/skills/workflows/issue/issue-lifecycle/scripts/manage_issue_lifecycle.sh`
- Subagent worktree + PR execution:
  - Scriptless contract using native `git` + `gh` commands (see `skills/workflows/issue/issue-subagent-pr/SKILL.md`)
- Main-agent PR review + issue sync:
  - `$AGENT_HOME/skills/workflows/issue/issue-pr-review/scripts/manage_issue_pr_review.sh`

## Issue delivery automation (main-agent orchestration CLI)

- Live GitHub-backed orchestration (issue and plan flows):
  - `plan-issue <subcommand>`
- Local rehearsal / dry-run orchestration (same subcommands, no GitHub writes):
  - `plan-issue-local <subcommand> --dry-run`
- Key subcommands:
  - `start-plan`, `start-sprint`, `ready-sprint`, `accept-sprint`, `status-plan`, `ready-plan`, `close-plan`

## Artifact output paths

- Create a project-scoped ad hoc artifact run directory:
  - `agent-out project --topic <topic> --mkdir`
- Audit `$AGENT_HOME/out/` for noncanonical top-level entries:
  - `agent-out audit --agent-home "$AGENT_HOME"`

## Web evidence

- Capture deterministic, redacted static HTTP evidence bundles for agent
  workflows:
  - Skill contract: `skills/tools/browser/web-evidence/SKILL.md`
  - `web-evidence capture <url> --out <dir> [--format text|json] [--label <label>]`
  - `web-evidence capture <url> --out <dir> [--method get|head]`
  - `web-evidence completion <bash|zsh>`
- Artifact contract: `summary.json`, `headers.redacted.json`, and
  `body-preview.redacted.txt` under the requested output directory.
- Version floor: requires the `nils-web-evidence` package from the `nils-cli`
  release that includes workspace version `0.8.3`.
- Scope boundary: this is static HTTP/HTTPS evidence only; use Browser, Chrome,
  Playwright, or future browser-session tooling for JavaScript execution,
  screenshots, cookies, authenticated sessions, console logs, or browser state.

## Edit-scope locks

- Create, read, validate, and clear deterministic edit-scope locks for agent
  workflows:
  - Skill contract: `skills/tools/devex/agent-scope-lock/SKILL.md`
  - `agent-scope-lock create --path <repo-relative-path> [--path <path> ...]`
  - `agent-scope-lock validate --changes all --format json`
  - `agent-scope-lock read --format json`
  - `agent-scope-lock clear`
- Version floor: requires the `nils-agent-scope-lock` package from the
  `nils-cli` release that includes workspace version `0.8.3`.
- Local checkout boundary: before that release is installed on PATH, consume the
  same command surface only through a validated local `nils-cli` checkout, for
  example `cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml -p
  nils-agent-scope-lock --bin agent-scope-lock -- <subcommand> ...` from the
  target git work tree.

## Test-first evidence

- Record deterministic test-first evidence or waivers for agent workflows:
  - Skill contract: `skills/tools/devex/test-first-evidence/SKILL.md`
  - `test-first-evidence init --out <dir> --classification <classification>`
  - `test-first-evidence record-failing --out <dir> --command <command> --exit-code <code> --summary <summary>`
  - `test-first-evidence record-waiver --out <dir> --reason <reason>`
  - `test-first-evidence record-final --out <dir> --command <command> --status pass|fail`
  - `test-first-evidence verify --out <dir> --format json`
  - `test-first-evidence show --out <dir> --format json`
- Artifact contract: `test-first-evidence.json` under the requested output
  directory, with record schema `test-first-evidence.record.v1`.
- Version floor: requires the `nils-test-first-evidence` package from the
  `nils-cli` release that includes that package.
- Local checkout boundary: before that release is installed on PATH, consume the
  same command surface only through a validated local `nils-cli` checkout, for
  example `cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml -p
  nils-test-first-evidence --bin test-first-evidence -- <subcommand> ...`.

## Agent workflow primitives

- Record and verify deterministic workflow evidence through the
  `nils-agent-workflow-primitives` package:
  - Skill contracts:
    - `skills/tools/browser/browser-session/SKILL.md`
    - `skills/tools/devex/canary-check/SKILL.md`
    - `skills/tools/devex/docs-impact/SKILL.md`
    - `skills/tools/devex/model-cross-check/SKILL.md`
    - `skills/tools/devex/review-evidence/SKILL.md`
  - `browser-session init|record-step|verify|show`
  - `canary-check run|verify|show`
  - `docs-impact scan`
  - `model-cross-check init|record-observation|verify|show`
  - `review-evidence init|record-finding|record-validation|verify|show`
- Artifact contracts:
  - `browser-session.json` with record schema `browser-session.record.v1`.
  - `canary-check.json` with record schema `canary-check.record.v1`.
  - `model-cross-check.json` with record schema `model-cross-check.record.v1`.
  - `review-evidence.json` with record schema `review-evidence.record.v1`.
  - `docs-impact` emits JSON scan results and does not write project files.
- Version floor: requires the `nils-agent-workflow-primitives` package from the
  `nils-cli` release that includes these binaries.
- Local checkout boundary: before that release is installed on PATH, consume the
  same command surfaces only through a validated local `nils-cli` checkout, for
  example `cargo run --locked --manifest-path /path/to/nils-cli/Cargo.toml -p
  nils-agent-workflow-primitives --bin docs-impact -- scan --format json`.
