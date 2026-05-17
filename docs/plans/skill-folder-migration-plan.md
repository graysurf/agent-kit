# Plan: Skill Folder Migration

## Overview

This plan migrates the public skill folder layout after the README catalog
boundary cleanup. The top-level public domains stay stable:
`skills/workflows/`, `skills/tools/`, and `skills/automation/`. The work only
rehomes overloaded areas such as `tools/devex` and flat automation folders into
clearer subareas, then updates references, tooling assumptions, and validation
coverage in the same branch.

## Scope

- In scope: tracked public skills under `skills/tools/` and
  `skills/automation/`, README catalogs, skill anatomy docs, tooling indexes,
  skill-management scripts/tests, and repo-local references to moved paths.
- In scope: compatibility notes for old paths during the migration window.
- Out of scope: changing skill behavior, changing public top-level domains,
  moving prompt-style skills, moving `skills/workflows/`, moving
  `skills/_projects/`, moving `skills/.system/`, or adding new automation.

## Assumptions

1. `skills/workflows/`, `skills/tools/`, and `skills/automation/` remain the
   only tracked public skill domains.
2. Directory moves use `git mv` so history remains traceable.
3. No compatibility symlinks are added unless skill discovery and validation
   are explicitly checked to accept them.
4. The migration starts from a clean branch after the README-only catalog
   clarification commit.
5. Old path mentions in historical docs are updated only when they describe the
   current contract, not when they intentionally describe past behavior.

## Proposed target map

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

## Sprint 1: Taxonomy And Tooling Guardrails

**Goal**: Make the repo explicitly accept nested skill subareas before any
folder moves.
**Demo/Validation**:

- Command(s): `scripts/check.sh --docs`, `scripts/check.sh --markdown`,
  `scripts/check.sh --tests -- -k tools_skill_management_create_skill`
- Verify: docs and create-skill tests describe the new area taxonomy and still
  generate README catalog rows correctly.

**PR grouping intent**: group
**Execution Profile**: serial

### Task 1.1: Document the target taxonomy

- **Location**:
  - `README.md`
  - `skills/README.md`
  - `docs/runbooks/skills/SKILLS_ANATOMY_V2.md`
  - `docs/runbooks/skills/TOOLING_INDEX_V2.md`
- **Description**: Add the target folder taxonomy and clarify that nested
  subareas such as `skills/tools/browser/evidence/<skill>` are valid when they
  express a real execution boundary.
- **Dependencies**: none
- **Complexity**: 3
- **Acceptance criteria**:
  - The three public domains stay unchanged.
  - The target map is documented once and referenced instead of duplicated.
  - The docs distinguish folder taxonomy from skill behavior.
- **Validation**:
  - `scripts/check.sh --docs`
  - `scripts/check.sh --markdown`

### Task 1.2: Harden README catalog insertion for nested areas

- **Location**:
  - `skills/tools/skill-management/create-skill/scripts/create_skill.sh`
  - `skills/tools/skill-management/create-skill/tests/test_tools_skill_management_create_skill.py`
- **Description**: Add focused coverage for nested tool and automation paths so
  new skills such as `skills/tools/workflow-evidence/example-skill` and
  `skills/automation/ci/example-skill` produce useful README Area labels.
- **Dependencies**:
  - Task 1.1
- **Complexity**: 3
- **Acceptance criteria**:
  - Existing direct-area paths still insert correctly.
  - New nested paths insert deterministic Area labels.
  - Non-public domains still skip README insertion.
- **Validation**:
  - `scripts/check.sh --tests -- -k tools_skill_management_create_skill`

### Task 1.3: Prepare a path reference audit checklist

- **Location**:
  - `docs/plans/skill-folder-migration-plan.md`
  - `docs/runbooks/skills/TOOLING_INDEX_V2.md`
- **Description**: Define the `rg` queries and review rules used before each
  move so old current-contract paths are updated without rewriting unrelated
  historical notes.
- **Dependencies**:
  - Task 1.1
- **Complexity**: 1
- **Acceptance criteria**:
  - The migration has a repeatable audit command for each moved directory.
  - Historical references are explicitly reviewed rather than blindly replaced.
- **Validation**:
  - `rg -n "skills/tools/devex|skills/automation/(gh-fix-ci|release-workflow|issue-delivery)" README.md docs skills tests`

## Sprint 2: Tool Folder Migration

**Goal**: Move overloaded tool folders into clearer bounded-tool areas without
changing skill behavior.
**Demo/Validation**:

- Command(s): `scripts/check.sh --contracts --skills-layout`,
  `scripts/check.sh --docs`, `scripts/check.sh --markdown`
- Verify: every moved tool skill validates, README links resolve, and no stale
  current-contract references point to old tool paths.

**PR grouping intent**: group
**Execution Profile**: parallel-x2

### Task 2.1: Move workflow evidence primitives

- **Location**:
  - `skills/tools/devex/canary-check/SKILL.md`
  - `skills/tools/devex/docs-impact/SKILL.md`
  - `skills/tools/devex/model-cross-check/SKILL.md`
  - `skills/tools/devex/review-evidence/SKILL.md`
  - `skills/tools/devex/skill-usage/SKILL.md`
  - `skills/tools/devex/test-first-evidence/SKILL.md`
  - `skills/tools/workflow-evidence/canary-check/SKILL.md`
- **Description**: Move deterministic evidence-recording skills from
  `tools/devex` into `tools/workflow-evidence`, then update SKILL.md
  entrypoint references, tests, README rows, and tooling indexes.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 5
- **Acceptance criteria**:
  - Evidence capture remains in nils-cli primitives; skills still own workflow
    judgment and policy.
  - All moved skills keep their tests and references intact.
  - No old path remains in current-contract docs.
- **Validation**:
  - `scripts/check.sh --contracts --skills-layout`
  - `scripts/check.sh --tests -- -k "canary_check or docs_impact or model_cross_check or review_evidence or skill_usage or test_first_evidence"`

### Task 2.2: Move scope, git, review, and notification helpers

- **Location**:
  - `skills/tools/devex/agent-scope-lock/SKILL.md`
  - `skills/tools/devex/semantic-commit/SKILL.md`
  - `skills/tools/devex/open-changed-files-review/SKILL.md`
  - `skills/tools/devex/desktop-notify/SKILL.md`
  - `skills/tools/scope/agent-scope-lock/SKILL.md`
  - `skills/tools/git/semantic-commit/SKILL.md`
  - `skills/tools/review/open-changed-files-review/SKILL.md`
  - `skills/tools/notifications/desktop-notify/SKILL.md`
- **Description**: Split the remaining `tools/devex` skills into narrower
  caller-owned tool areas.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 3
- **Acceptance criteria**:
  - `semantic-commit` remains a bounded staged-commit tool.
  - `agent-scope-lock` remains a mechanical edit-boundary tool.
  - Review and notification helpers do not become automation workflows.
- **Validation**:
  - `scripts/check.sh --contracts --skills-layout`
  - `scripts/check.sh --tests -- -k "agent_scope_lock or semantic_commit or open_changed_files_review or desktop_notify"`

### Task 2.3: Split browser and app runtime folders

- **Location**:
  - `skills/tools/agent-doc-init/SKILL.md`
  - `skills/tools/macos-agent-ops/SKILL.md`
  - `skills/tools/browser/agent-browser/SKILL.md`
  - `skills/tools/browser/browser-session/SKILL.md`
  - `skills/tools/browser/playwright/SKILL.md`
  - `skills/tools/browser/web-evidence/SKILL.md`
  - `skills/tools/browser/web-qa/SKILL.md`
  - `skills/tools/agent-docs/agent-doc-init/SKILL.md`
  - `skills/tools/app-runtime/macos-agent-ops/SKILL.md`
  - `skills/tools/browser/runtime/playwright/SKILL.md`
  - `skills/tools/browser/evidence/web-evidence/SKILL.md`
- **Description**: Move direct tool folders and browser skills into the
  taxonomy that README already exposes: runtime execution surfaces separate
  from retained browser evidence.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 5
- **Acceptance criteria**:
  - Runtime browser tools stay distinct from evidence-recording tools.
  - Agent-doc bootstrap and macOS app runtime no longer sit as flat one-off
    folders under `skills/tools/`.
  - Browser-related tests and references still resolve.
- **Validation**:
  - `scripts/check.sh --contracts --skills-layout`
  - `scripts/check.sh --tests -- -k "agent_doc_init or macos_agent_ops or browser_session or web_evidence or web_qa or playwright or agent_browser"`

## Sprint 3: Automation Folder Migration

**Goal**: Move flat automation skills into areas that reflect the loop they own:
commit, issue delivery, CI repair, bug work, security scan, and release.
**Demo/Validation**:

- Command(s): `scripts/check.sh --contracts --skills-layout`,
  `scripts/check.sh --docs`, `scripts/check.sh --markdown`
- Verify: automation skills still read as end-to-end loop owners and all old
  current-contract path references are removed.

**PR grouping intent**: group
**Execution Profile**: parallel-x2

### Task 3.1: Move commit and issue delivery automation

- **Location**:
  - `skills/automation/semantic-commit-autostage/SKILL.md`
  - `skills/automation/issue-delivery/SKILL.md`
  - `skills/automation/plan-issue-delivery/SKILL.md`
  - `skills/automation/commit/semantic-commit-autostage/SKILL.md`
  - `skills/automation/issue/issue-delivery/SKILL.md`
  - `skills/automation/issue/plan-issue-delivery/SKILL.md`
- **Description**: Move commit automation and issue-delivery loop skills into
  target subareas, then update references in issue workflows, plan-issue
  runtime adapter docs, README, and tests.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 5
- **Acceptance criteria**:
  - `semantic-commit-autostage` remains automation because it owns staging.
  - Issue delivery skills remain distinct from issue workflow primitives.
  - Runtime adapter docs use the new paths.
- **Validation**:
  - `scripts/check.sh --contracts --skills-layout`
  - `scripts/check.sh --tests -- -k "semantic_commit_autostage or issue_delivery or plan_issue_delivery"`

### Task 3.2: Move CI, bug, security, and release automation

- **Location**:
  - `skills/automation/gh-fix-ci/SKILL.md`
  - `skills/automation/fix-bug-pr/SKILL.md`
  - `skills/automation/find-and-fix-bugs/SKILL.md`
  - `skills/automation/semgrep-find-and-fix/SKILL.md`
  - `skills/automation/release-workflow/SKILL.md`
  - `skills/automation/ci/gh-fix-ci/SKILL.md`
  - `skills/automation/bug/find-and-fix-bugs/SKILL.md`
  - `skills/automation/security/semgrep-find-and-fix/SKILL.md`
  - `skills/automation/release/release-workflow/SKILL.md`
- **Description**: Move the remaining flat automation skills into target areas
  that match the README Area labels.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 5
- **Acceptance criteria**:
  - CI repair, bug repair/discovery, Semgrep, and release workflows stay under
    `automation`, not `tools`.
  - Release helper paths and response templates still resolve.
  - README catalog links match the moved folders.
- **Validation**:
  - `scripts/check.sh --contracts --skills-layout`
  - `scripts/check.sh --tests -- -k "gh_fix_ci or fix_bug_pr or find_and_fix_bugs or semgrep_find_and_fix or release_workflow"`

## Sprint 4: Compatibility Cleanup And Full Gate

**Goal**: Remove migration residue and prove the new layout is the only current
contract.
**Demo/Validation**:

- Command(s): `scripts/check.sh --all`
- Verify: full repo gate passes and no stale current-contract path remains.

**PR grouping intent**: per-sprint
**Execution Profile**: serial

### Task 4.1: Run stale path and entrypoint audits

- **Location**:
  - `README.md`
  - `docs/runbooks/skills/TOOLING_INDEX_V2.md`
  - `skills/README.md`
  - `scripts/ci/stale-skill-scripts-audit.sh`
  - `tests/conftest.py`
- **Description**: Run broad `rg` audits for old paths, review each hit, and
  update only current-contract references.
- **Dependencies**:
  - Task 2.1
  - Task 2.2
  - Task 2.3
  - Task 3.1
  - Task 3.2
- **Complexity**: 3
- **Acceptance criteria**:
  - No stale current-contract references to old paths remain.
  - Historical notes are either updated or clearly left as history.
  - Entry-point ownership checks pass.
- **Validation**:
  - `rg -n "skills/tools/devex" README.md docs skills tests scripts`
  - `rg -n "skills/tools/browser/(agent-browser|browser-session|playwright|web-evidence|web-qa)" README.md docs skills tests scripts`
  - `rg -n "skills/automation/(gh-fix-ci|release-workflow|issue-delivery)" README.md docs skills tests scripts`
  - `rg -n "skills/automation/(plan-issue-delivery|semantic-commit-autostage)" README.md docs skills tests scripts`
  - `rg -n "skills/automation/(find-and-fix-bugs|fix-bug-pr|semgrep-find-and-fix)" README.md docs skills tests scripts`
  - `bash scripts/ci/stale-skill-scripts-audit.sh --check`
  - `scripts/check.sh --entrypoint-ownership`

### Task 4.2: Run final repository validation

- **Location**:
  - `scripts/check.sh`
  - `.github/workflows/lint.yml`
- **Description**: Run the full validation gate and fix any breakage caused by
  moved paths.
- **Dependencies**:
  - Task 4.1
- **Complexity**: 3
- **Acceptance criteria**:
  - `scripts/check.sh --all` passes.
  - Any CI-specific generated phase mappings remain unchanged unless a path move
    requires an intentional update.
- **Validation**:
  - `scripts/check.sh --all`

## Testing Strategy

- Unit: run focused pytest selections for moved skill tests after each sprint.
- Integration: run contract/layout checks after each directory move batch.
- Docs: run `scripts/check.sh --docs` and `scripts/check.sh --markdown` after
  every sprint.
- Repository gate: run `scripts/check.sh --all` before reporting the migration
  complete.

## Risks & gotchas

- Moving skill folders can break skill discovery, README links, hook allow-lists,
  and test fixtures even when SKILL.md content is unchanged.
- `create-skill` currently maps only the three public README sections; preserve
  that boundary while allowing nested Area labels.
- `plan-issue-delivery` and browser skills have many nested references and are
  likely overlap hotspots.
- Blind search-and-replace can corrupt historical docs. Review old-path hits
  before editing them.
- Symlinks or duplicate compatibility folders may confuse layout audits and
  should be avoided unless explicitly validated.

## Rollback plan

- Revert each sprint commit independently if validation fails after that sprint.
- If a move batch is partially applied, use `git mv` to restore the old path and
  rerun `scripts/check.sh --contracts --skills-layout`.
- If README/catalog tooling changes are valid but a later move is risky, keep
  Sprint 1 and postpone the folder moves.
