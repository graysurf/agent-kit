# Skill Folder Migration Review Source

Status: plan source artifact for implementation planning
Date: 2026-05-17
Source: review of the README skill catalog taxonomy and current `skills/`
directory layout.
Intended next artifact: `docs/plans/skill-folder-migration-plan.md`

## Purpose

Capture the judgment behind the skill folder migration before execution
planning. The plan should control sequencing, dependencies, PR grouping, and
validation; this source document owns the rationale, target taxonomy, and
guardrails.

## Current Judgment

The public top-level domains should stay stable:

- `skills/workflows/`: agent-owned workflows and conversation/reporting flows.
- `skills/tools/`: bounded tools, wrappers, evidence primitives, and mechanical
  helpers.
- `skills/automation/`: end-to-end loops that own repeated orchestration or
  remediation.

The improvement needed is below those domains. Several current folders are
overloaded or too flat, which makes README Area labels clearer than the
underlying folder layout.

## Findings

| Priority | Issue | Evidence | Fix location | Acceptance |
| --- | --- | --- | --- | --- |
| P1 | `skills/tools/devex/` mixes unrelated tool boundaries. | README now distinguishes workflow evidence, scope/git, review UX, and notifications, but current paths still collapse them into `devex`. | `skills/tools/devex/*`, `skills/tools/workflow-evidence/`, `skills/tools/scope/`, `skills/tools/git/`, `skills/tools/review/`, `skills/tools/notifications/` | Each moved tool has a folder that matches its behavior boundary, and old current-contract references are updated. |
| P1 | `skills/automation/` is too flat for distinct loops. | README Area labels distinguish commit automation, issue delivery, CI repair, bug work, security scan, and release. | `skills/automation/*`, `skills/automation/commit/`, `skills/automation/issue/`, `skills/automation/ci/`, `skills/automation/bug/`, `skills/automation/security/`, `skills/automation/release/` | Automation skills remain automation, but grouped by the loop they own. |
| P2 | Browser runtime and browser evidence live in one direct folder. | Runtime tools such as `playwright` and evidence workflows such as `web-evidence` have different responsibilities. | `skills/tools/browser/*`, `skills/tools/browser/runtime/`, `skills/tools/browser/evidence/` | Runtime execution and retained evidence are visibly separate. |
| P2 | Direct one-off tool folders obscure their category. | `agent-doc-init` and `macos-agent-ops` sit directly under `skills/tools/` even though README already implies clearer areas. | `skills/tools/agent-doc-init/`, `skills/tools/macos-agent-ops/`, `skills/tools/agent-docs/`, `skills/tools/app-runtime/` | Direct folders move under a named tool area without behavior changes. |
| P2 | Tooling must support nested skill areas before moves. | `create-skill` README insertion and skill anatomy docs are the likely first breakpoints for nested areas. | `skills/tools/skill-management/create-skill/`, `docs/runbooks/skills/SKILLS_ANATOMY_V2.md`, `docs/runbooks/skills/TOOLING_INDEX_V2.md` | Nested tool and automation paths validate and generate deterministic README Area labels. |

## Target Folder Map

| Current path | Target path |
| --- | --- |
| `skills/tools/agent-doc-init/` | `skills/tools/agent-docs/agent-doc-init/` |
| `skills/tools/macos-agent-ops/` | `skills/tools/app-runtime/macos-agent-ops/` |
| `skills/tools/browser/playwright/` | `skills/tools/browser/runtime/playwright/` |
| `skills/tools/browser/agent-browser/` | `skills/tools/browser/runtime/agent-browser/` |
| `skills/tools/browser/browser-session/` | `skills/tools/browser/evidence/browser-session/` |
| `skills/tools/browser/web-evidence/` | `skills/tools/browser/evidence/web-evidence/` |
| `skills/tools/browser/web-qa/` | `skills/tools/browser/evidence/web-qa/` |
| `skills/tools/devex/agent-scope-lock/` | `skills/tools/scope/agent-scope-lock/` |
| `skills/tools/devex/semantic-commit/` | `skills/tools/git/semantic-commit/` |
| `skills/tools/devex/open-changed-files-review/` | `skills/tools/review/open-changed-files-review/` |
| `skills/tools/devex/desktop-notify/` | `skills/tools/notifications/desktop-notify/` |
| `skills/tools/devex/canary-check/` | `skills/tools/workflow-evidence/canary-check/` |
| `skills/tools/devex/docs-impact/` | `skills/tools/workflow-evidence/docs-impact/` |
| `skills/tools/devex/model-cross-check/` | `skills/tools/workflow-evidence/model-cross-check/` |
| `skills/tools/devex/review-evidence/` | `skills/tools/workflow-evidence/review-evidence/` |
| `skills/tools/devex/skill-usage/` | `skills/tools/workflow-evidence/skill-usage/` |
| `skills/tools/devex/test-first-evidence/` | `skills/tools/workflow-evidence/test-first-evidence/` |
| `skills/automation/semantic-commit-autostage/` | `skills/automation/commit/semantic-commit-autostage/` |
| `skills/automation/issue-delivery/` | `skills/automation/issue/issue-delivery/` |
| `skills/automation/plan-issue-delivery/` | `skills/automation/issue/plan-issue-delivery/` |
| `skills/automation/gh-fix-ci/` | `skills/automation/ci/gh-fix-ci/` |
| `skills/automation/fix-bug-pr/` | `skills/automation/bug/fix-bug-pr/` |
| `skills/automation/find-and-fix-bugs/` | `skills/automation/bug/find-and-fix-bugs/` |
| `skills/automation/semgrep-find-and-fix/` | `skills/automation/security/semgrep-find-and-fix/` |
| `skills/automation/release-workflow/` | `skills/automation/release/release-workflow/` |

## Ownership Boundary

- Tools remain bounded helpers or evidence primitives. They should not start
  owning multi-step remediation loops just because they move folders.
- Automation remains loop ownership. It can stage, retry, monitor, repair, or
  orchestrate across steps when that is the skill's contract.
- The migration changes layout and references only. It should not change
  skill behavior, external commands, hook policy, or user-facing workflow
  contracts unless a path reference requires it.

## Backlog

- Teach skill-management tooling and docs that nested public skill areas are
  valid when the area expresses a real behavior boundary.
- Move tool folders in batches that minimize same-file README and tooling-index
  conflicts.
- Move automation folders after tool nested-area support is proven.
- Audit old path references after every batch and update only current-contract
  references.
- Run the full repository gate before declaring the migration complete.

## Validation Gate

- `scripts/check.sh --contracts --skills-layout`
- `scripts/check.sh --docs`
- `scripts/check.sh --markdown`
- Focused pytest selections for moved skill groups.
- `bash scripts/ci/stale-skill-scripts-audit.sh --check`
- `scripts/check.sh --entrypoint-ownership`
- `scripts/check.sh --all`

## Retention Intent

This file is execution coordination under `docs/plans/`. Delete it with the
plan after the migration completes unless the target map or boundary guidance
is intentionally promoted into a maintained runbook.

## Guardrails

- Use `git mv` for moves so history remains traceable.
- Do not add compatibility symlinks unless skill discovery and layout audits
  explicitly validate them.
- Do not blindly search-and-replace historical notes. Update old paths when
  they describe current contracts; leave intentional history alone.
- Do not move `skills/workflows/`, `skills/_projects/`, or `skills/.system/`
  as part of this migration.
- Keep the target map in this source artifact. The plan may reference it but
  should stay focused on execution flow.

## Open Questions

- None. Compatibility aliases remain out of scope unless validation proves a
  concrete need during execution.
