# agent-kit

<!-- markdownlint-disable-file MD060 -->

agent-kit tracks AI agent setup to keep workflows consistent across machines. It contains prompt-style skills, custom workflows, and local
tooling.

## 🧭 Positioning

agent-kit is an opinionated agent workflow distribution, not a generic skill marketplace. It packages reusable skills, prompt-style skills,
home-scope policy, validation gates, delivery automation, and local setup conventions for Codex-style agent work.

The portable core is the tracked repository content: [AGENTS.md](./AGENTS.md),
[DEVELOPMENT.md](./DEVELOPMENT.md), [docs/](./docs), [scripts/](./scripts),
[hooks/](./hooks), and public skills under [skills/workflows/](skills/workflows), [skills/tools/](skills/tools), and
[skills/automation/](skills/automation). Project, company, system, and local overlays are supported, but they are not part of the portable
core unless they are explicitly tracked and documented.

Best fit:

- Engineers or teams who want agents to follow one validated operating model.
- Daily multi-repo work where preflight, checks, semantic commits, PR/MR
  delivery, release flow, and repeatable tooling matter.
- Users who prefer explicit guardrails over a loose collection of standalone
  prompt snippets.

## 🗂️ Project Structure

```text
.
├── .agents/    # repo-local agent helper scripts, including release entrypoint
├── .github/    # CI workflows (GitHub Actions)
├── docker/     # Docker image docs and workspace launcher pointers
├── docs/       # runbooks, plans, and testing docs
├── hooks/      # Codex hook source and managed config block
├── scripts/    # validation, sync, build, and helper entrypoints
├── skills/     # tracked public skills, prompt-style skills, and ignored overlays
├── tests/      # pytest regression/smoke tests
├── AGENTS.md   # global agent rules (response/tooling)
└── DEVELOPMENT.md
```

## ⚙️ Setup

Install agent-kit CLI tooling via the Homebrew tap:

```zsh
brew tap sympoies/tap
brew install nils-cli
```

Upgrade when needed:

```zsh
brew upgrade nils-cli
```

Set `AGENT_HOME` in `$HOME/.zshenv`:

```zsh
export AGENT_HOME="$HOME/.agents"
```

`AGENT_HOME` is the home for this agent-kit toolchain. Note: `nils-cli` ≥ 0.8.0
binaries (`agent-docs`, `plan-issue`) no longer auto-read `AGENT_HOME`. Pass the
home explicitly via `agent-docs --docs-home "$AGENT_HOME"` and
`plan-issue --state-dir "$AGENT_HOME"`, or export `AGENT_DOCS_HOME` /
`PLAN_ISSUE_HOME` alongside `AGENT_HOME`.

`nils-cli` also provides shared helper binaries used by skills and checks, including
`plan-tooling`, `api-*`, `semantic-commit`, `agent-out`, and media tooling.

Optional: set `PROJECT_PATH` per project (e.g. in a repo’s `.envrc`) so tools can treat that repo as the active project context:

```zsh
export PROJECT_PATH="$PWD"
```

For new repositories with missing policy baseline docs, run the canonical bootstrap flow:

```zsh
$AGENT_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh --dry-run --project-path "$PROJECT_PATH"
$AGENT_HOME/skills/tools/agent-doc-init/scripts/agent_doc_init.sh --apply --project-path "$PROJECT_PATH"
agent-docs --docs-home "$AGENT_HOME" baseline --check --target all --strict --project-path "$PROJECT_PATH" --format text
```

See [docs/runbooks/agent-docs/new-project-bootstrap.md](./docs/runbooks/agent-docs/new-project-bootstrap.md) for the full sequence.

Codex hooks are tracked under `hooks/codex/`, but the full
`$HOME/.codex/config.toml` file stays local-only. Sync the managed hook block
into the local config with:

```zsh
$AGENT_HOME/scripts/codex-hooks-sync sync --apply
```

## 🚦 New User Path

For a first install or handoff, keep the path short:

1. Install `nils-cli` and set `AGENT_HOME`.
2. Run `agent-docs --docs-home "$AGENT_HOME" resolve --context startup --strict --format checklist`.
3. From this repository, run `scripts/check.sh --all`.
4. Try one focused workflow, such as `agent-doc-init` in a disposable project.
5. Add project-local `.agents/skills` or private `skills/_projects` overlays only after the portable core works.

## 🐳 Docker And Workspace Environments

See [docker/agent-env/README.md](docker/agent-env/README.md) for the Ubuntu Docker environment, Docker Hub publish steps, and compose usage.
See [docker/agent-workspace-launcher/README.md](docker/agent-workspace-launcher/README.md) for the host-native
`agent-workspace-launcher` runtime that replaced legacy Docker wrapper usage.

## 🧰 Prompts

Prompt presets are implemented as prompt-style skills so Codex CLI can surface
them through `/skills`. The source prompt text lives under each skill's
`references/prompts/` directory.

### Common

| Prompt | Description | Usage |
| --- | --- | --- |
| [actionable-advice](./skills/workflows/prompts/actionable-advice/) | Answer a question with clarifying questions, multiple options, and a single recommendation | Use the `actionable-advice` skill |
| [actionable-knowledge](./skills/workflows/prompts/actionable-knowledge/) | Answer a learning/knowledge question with multiple explanation paths and a single recommended path | Use the `actionable-knowledge` skill |
| [orchestrator-first](./skills/workflows/prompts/orchestrator-first/) | Make the main agent own intent, dispatch, integration, validation, and final synthesis while subagents own lanes | Use the `orchestrator-first` skill |
| [parallel-first](./skills/workflows/prompts/parallel-first/) | Enable a parallel-first execution policy for this conversation thread when delegation is safe | Use the `parallel-first` skill |
| [test-first](./skills/workflows/prompts/test-first/) | Require failing-test evidence or an explicit waiver before production behavior changes | Use the `test-first` skill |

## 🛠️ Skills

### Skill management

See [skills/tools/skill-management/README.md](./skills/tools/skill-management/README.md) for how to create/validate/remove skills (including
project-local `.agents/skills`) using canonical entrypoints.

The catalog below covers tracked public skills under [skills/workflows/](skills/workflows),
[skills/tools/](skills/tools), and [skills/automation/](skills/automation). Tool skills may also be
grouped by execution surface, such as `skills/tools/computer-use/` for live GUI automation.
Prompt-style skills are listed in the Prompts section above and are not duplicated in the general workflow table.
Ignored local/system overlays may exist under `skills/_projects/` and `skills/.system/`, but they are
not part of the public catalog unless explicitly tracked.

### Workflows

| Area | Skill | Description |
| --- | --- | --- |
| Conversation | [requirements-gap-scan](./skills/workflows/conversation/requirements-gap-scan/) | Explicit requirements gap scan and blocking-clarification question format with suggested defaults                                         |
| Conversation | [handoff-session-prompt](./skills/workflows/conversation/handoff-session-prompt/) | Generate a generic next-session initialization prompt from the user request, conversation context, and any user-specified reference files without embedding project-specific details. |
| Conversation | [review-to-improvement-doc](./skills/workflows/conversation/review-to-improvement-doc/) | Convert review findings, risks, lessons learned, or follow-up backlog into a durable repo-local improvement document. |
| Conversation | [discussion-to-implementation-doc](./skills/workflows/conversation/discussion-to-implementation-doc/) | Convert completed requirements, design, feasibility, or customer-facing discussion into a durable implementation-readiness document. |
| Planning     | [create-plan](./skills/workflows/plan/create-plan/)                                                 | Create a comprehensive, phased implementation plan and save it under docs/plans/                                                          |
| Planning     | [create-plan-rigorous](./skills/workflows/plan/create-plan-rigorous/)                               | Create an extra-thorough implementation plan and get a subagent review                                                                    |
| Planning     | [docs-plan-cleanup](./skills/workflows/plan/docs-plan-cleanup/)                                     | Prune outdated docs/plans markdown with dry-run-first safeguards and related-doc reconciliation                                           |
| Planning     | [execute-plan-parallel](./skills/workflows/plan/execute-plan-parallel/)                             | Execute a markdown plan by spawning parallel subagents for unblocked tasks, then validate                                                 |
| Planning     | [execute-from-implementation-doc](./skills/workflows/plan/execute-from-implementation-doc/)                 | Resume and execute long-running implementation work from a durable execution-ready document and progress state                  |
| Planning     | [durable-artifact-cleanup](./skills/workflows/plan/durable-artifact-cleanup/)                       | Audit and remove obsolete durable implementation artifacts after execution is complete                              |
| Issue        | [issue-follow-up](./skills/workflows/issue/issue-follow-up/)                                        | Open or continue GitHub issues as durable follow-up timelines, routing to issue lifecycle, implementation, or PR workflows as needed       |
| Issue        | [issue-lifecycle](./skills/workflows/issue/issue-lifecycle/)                                        | Main-agent workflow for opening, maintaining, decomposing, and closing GitHub Issues as the planning source of truth                      |
| Issue        | [issue-subagent-pr](./skills/workflows/issue/issue-subagent-pr/)                                    | Subagent workflow for assigned task-lane implementation (pr-shared/per-sprint/pr-isolated), draft PR creation, and review-response updates linked to the owning issue |
| Issue        | [issue-pr-review](./skills/workflows/issue/issue-pr-review/)                                        | Main-agent PR review workflow with explicit PR comment links mirrored to the issue timeline                                               |
| Reporting    | [daily-brief](./skills/workflows/reporting/daily-brief/)                                            | Prepare a source-grounded daily information brief by orchestrating topic-radar JSON with stable preferences, concise user-language synthesis, and optional local history records |
| MR / GitLab | [create-gitlab-mr](./skills/workflows/mr/gitlab/create-gitlab-mr/)                                  | Create GitLab Merge Requests through an audited glab workflow with a standard MR body and explicit source-branch policy                   |
| MR / GitLab | [deliver-gitlab-mr](./skills/workflows/mr/gitlab/deliver-gitlab-mr/)                                | Deliver GitLab merge requests end to end with preflight, creation, pipeline wait/fix loop, close, and cleanup                             |
| MR / GitLab | [close-gitlab-mr](./skills/workflows/mr/gitlab/close-gitlab-mr/)                                    | Merge and close GitLab merge requests after pipeline gating, draft readiness, and branch cleanup                                          |
| PR / GitHub | [create-github-pr](./skills/workflows/pr/github/create-github-pr/)                                  | Create GitHub pull requests through the canonical provider-scoped workflow with audited hook bypass markers                               |
| PR / GitHub | [deliver-github-pr](./skills/workflows/pr/github/deliver-github-pr/)                                | Deliver GitHub pull requests end to end with preflight, creation, CI wait/fix loop, merge, and cleanup                                    |
| PR / GitHub | [close-github-pr](./skills/workflows/pr/github/close-github-pr/)                                    | Merge and close GitHub pull requests after PR hygiene review and branch cleanup                                                           |
| PR / Plan Issue | [create-plan-issue-sprint-pr](./skills/workflows/pr/plan-issue/create-plan-issue-sprint-pr/) | Open a draft GitHub sprint PR for a plan-issue implementation lane using the canonical sprint PR body schema and assigned dispatch record |

### Tools

| Area | Skill | Description |
| --- | --- | --- |
| Agent Docs       | [agent-doc-init](./skills/tools/agent-doc-init/)                                           | Initialize missing baseline docs safely (dry-run first), then upsert optional project extension entries         |
| App Ops          | [macos-agent-ops](./skills/tools/macos-agent-ops/)                                         | Run repeatable macOS app checks/scenarios with `macos-agent`                                                    |
| Browser          | [playwright](./skills/tools/browser/playwright/)                                           | Automate a real browser via Playwright CLI using the wrapper script                                             |
| Browser          | [agent-browser](./skills/tools/browser/agent-browser/)                                     | Optional legacy fallback for agent-browser CLI automation when native Browser/Chrome tools are unavailable      |
| Browser          | [browser-session](./skills/tools/browser/browser-session/)                                 | Record browser-session goals, steps, statuses, and evidence artifacts through the nils-cli `browser-session` command |
| Browser          | [web-evidence](./skills/tools/browser/web-evidence/)                                       | Capture redacted static HTTP evidence bundles through the nils-cli `web-evidence` command                      |
| Skill Management | [skill-governance](./skills/tools/skill-management/skill-governance/)                      | Audit skill layout and validate SKILL.md contracts                                                              |
| Skill Management | [create-skill](./skills/tools/skill-management/create-skill/)                              | Scaffold a new skill directory that passes skill-governance audit and contract validation                       |
| Skill Management | [create-project-skill](./skills/tools/skill-management/create-project-skill/)              | Scaffold a project-local skill under `<project>/.agents/skills/` with contract/layout validation                |
| Skill Management | [remove-skill](./skills/tools/skill-management/remove-skill/)                              | Remove a tracked skill directory and purge non-archived repo references (breaking change)                       |
| DevEx            | [agent-scope-lock](./skills/tools/devex/agent-scope-lock/)                                 | Create, read, validate, and clear edit-scope locks through the nils-cli `agent-scope-lock` command              |
| DevEx            | [canary-check](./skills/tools/devex/canary-check/)                                         | Run a local canary command and persist redacted pass/fail evidence through the nils-cli `canary-check` command |
| DevEx            | [docs-impact](./skills/tools/devex/docs-impact/)                                           | Scan Git changes for documentation impact through the nils-cli `docs-impact` command                           |
| DevEx            | [model-cross-check](./skills/tools/devex/model-cross-check/)                               | Record primary/checker model observations through the nils-cli `model-cross-check` command                     |
| DevEx            | [review-evidence](./skills/tools/devex/review-evidence/)                                   | Record review findings and final validation through the nils-cli `review-evidence` command                     |
| DevEx            | [test-first-evidence](./skills/tools/devex/test-first-evidence/)                           | Record failing-test evidence, waivers, and final validation through the nils-cli `test-first-evidence` command |
| DevEx            | [semantic-commit](./skills/tools/devex/semantic-commit/)                                   | Commit staged changes using Semantic Commit format                                                              |
| DevEx            | [open-changed-files-review](./skills/tools/devex/open-changed-files-review/)               | Open files edited by Codex in VSCode after making changes (silent no-op when unavailable)                       |
| DevEx            | [desktop-notify](./skills/tools/devex/desktop-notify/)                                     | Send desktop notifications via terminal-notifier (macOS) or notify-send (Linux)                                 |
| Media            | [image-processing](./skills/tools/media/image-processing/)                                 | Convert `svg/png/jpg/jpeg/webp` inputs to `png/webp/jpg` and validate SVGs via `image-processing`              |
| Media            | [screen-record](./skills/tools/media/screen-record/)                                       | Record a single window or full display to a video file via the screen-record CLI (macOS 12+ and Linux)          |
| Media            | [screenshot](./skills/tools/media/screenshot/)                                             | Capture screenshots via screen-record on macOS and Linux, with optional macOS desktop capture via screencapture |
| SQL              | [sql](./skills/tools/sql/sql/)                                                             | Run PostgreSQL, MySQL, or SQL Server queries through one dialect subcommand and prefix + env file convention    |
| Testing          | [api-test-runner](./skills/tools/testing/api-test-runner/)                                 | Canonical REST + GraphQL API testing skill: suites via `api-test`, focused calls via `api-rest` / `api-gql`     |
| Computer Use     | [google-sheets-cell-edit](./skills/tools/computer-use/google-sheets-cell-edit/) | Edit Google Sheets cells through browser automation with reliable cell targeting, multiline content, partial rich-text hyperlinks, and in-app validation. |
| Market Research | [polymarket-readonly](./skills/tools/market-research/polymarket-readonly/) | Research Polymarket markets through read-only public APIs and MCP servers without trading credentials. |
| Market Research | [topic-radar](./skills/tools/market-research/topic-radar/) | Aggregate read-only AI and technology trend signals with a personal AI/Tech profile, fast `ai-news` preset, Polymarket MCP input, and Markdown or JSON digests. |

### Automation

| Area | Skill | Description |
| --- | --- | --- |
| DevEx       | [semantic-commit-autostage](./skills/automation/semantic-commit-autostage/) | Autostage (git add) and commit changes using Semantic Commit format for fully automated workflows                                                                                          |
| Issue       | [issue-delivery](./skills/automation/issue-delivery/)                       | Orchestrate issue execution loops end-to-end: open issue, track status, request review, and close only after approval + merged PR gates                                                    |
| Issue       | [plan-issue-delivery](./skills/automation/plan-issue-delivery/)             | Orchestrate plan-driven issue delivery by sprint: split plan tasks, dispatch subagent PR work, enforce acceptance gates, and advance to the next sprint without main-agent implementation. |
| Maintenance | [gh-fix-ci](./skills/automation/gh-fix-ci/)                                 | Automatically fix failing GitHub Actions checks, semantic-commit-autostage + push, and retry until green                                                                                   |
| Maintenance | [fix-bug-pr](./skills/automation/fix-bug-pr/)                               | Find bug-type PRs with unresolved bug items, fix and push updates, comment, and keep PR body status synced                                                                                 |
| Maintenance | [find-and-fix-bugs](./skills/automation/find-and-fix-bugs/)                 | Find, triage, and fix bugs; open a PR with a standard template                                                                                                                             |
| Maintenance | [semgrep-find-and-fix](./skills/automation/semgrep-find-and-fix/)           | Scan a repo using its local Semgrep config, triage findings, and open a fix PR or report-only PR                                                                                           |
| Release     | [release-workflow](./skills/automation/release-workflow/)                   | Execute project release workflows by following a repo release guide (with a bundled fallback)                                                                                              |

## 🧪 Local and CI Check Entrypoints

Use `scripts/check.sh` as the canonical local check entrypoint:

```bash
scripts/check.sh --pre-commit
```

Use `scripts/check.sh --all` as the canonical minimum gate.

Common focused runs:

```bash
scripts/check.sh --docs
scripts/check.sh --markdown
scripts/check.sh --tests -- -m script_smoke
bash scripts/ci/stale-skill-scripts-audit.sh --check
scripts/check.sh --entrypoint-ownership
```

Lint CI (`.github/workflows/lint.yml`) maps its phases to
`scripts/check.sh` modes.
Generated phase blocks are managed by
`scripts/ci/generate-lint-workflow-phases.py`
(`--check` for CI, `--write` when updating mappings).
Keep docs and CI guidance aligned with these modes instead of legacy
ad-hoc wrappers.

## 🪪 License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This project is licensed under the MIT License. See [LICENSE](LICENSE).
