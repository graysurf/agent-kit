# Plan: Skill Folder Migration

## Overview

Migrate the public skill folder layout below the existing top-level domains.
The migration keeps `skills/workflows/`, `skills/tools/`, and
`skills/automation/` stable while moving overloaded subareas into folders that
match the catalog taxonomy. The source artifact owns the rationale and target
map; this plan owns execution order, dependencies, and validation gates.

## Read First

- Primary source:
  `docs/plans/skill-folder-migration-review-source.md`
- Source type: `review-to-improvement-doc`
- Open questions carried into execution: none

## Scope

- In scope: tracked public skills under `skills/tools/` and
  `skills/automation/`, README catalog rows, skill anatomy docs, tooling
  indexes, skill-management scripts/tests, and current-contract references to
  moved paths.
- In scope: repeated stale-path audits after each move batch.
- Out of scope: skill behavior changes, public top-level domain changes,
  prompt-style skill moves, `skills/workflows/`, `skills/_projects/`,
  `skills/.system/`, compatibility symlinks, and new automation.

## Assumptions

1. The target folder map in the primary source artifact is the migration map.
2. Directory moves use `git mv` so history remains traceable.
3. No compatibility symlinks are added unless validation proves a concrete
   need.
4. Current-contract path references are updated; intentional historical notes
   are left alone or explicitly labeled as history.
5. Each sprint lands with docs, markdown, and relevant skill validation passing.

## Sprint 1: Nested Area Readiness

**Goal**: Make nested public skill areas explicit and testable before moving
folders.
**Demo/Validation**:

- Command(s): `scripts/check.sh --docs`, `scripts/check.sh --markdown`,
  `scripts/check.sh --tests -- -k tools_skill_management_create_skill`
- Verify: docs and create-skill coverage accept nested tool and automation
  areas while preserving the three public top-level domains.

**PR grouping intent**: group
**Execution Profile**: serial

### Task 1.1: Document nested area rules

- **Location**:
  - `README.md`
  - `skills/README.md`
  - `docs/runbooks/skills/SKILLS_ANATOMY_V2.md`
  - `docs/runbooks/skills/TOOLING_INDEX_V2.md`
  - `docs/plans/skill-folder-migration-review-source.md`
- **Description**: Document nested area rules and link the target map source.
- **Dependencies**:
  - none
- **Complexity**: 3
- **Acceptance criteria**:
  - The three public domains remain the only public top-level domains.
  - Nested areas are described as folder taxonomy, not behavior changes.
  - The source artifact is the single target-map copy.
- **Validation**:
  - `scripts/check.sh --docs`
  - `scripts/check.sh --markdown`

### Task 1.2: Support nested README Area labels

- **Location**:
  - `skills/tools/skill-management/create-skill/scripts/create_skill.sh`
  - `skills/tools/skill-management/create-skill/tests/test_tools_skill_management_create_skill.py`
  - `README.md`
- **Description**: Add create-skill coverage for nested public skill paths.
- **Dependencies**:
  - Task 1.1
- **Complexity**: 3
- **Acceptance criteria**:
  - Existing direct-area paths still insert correctly.
  - Nested tool and automation paths insert deterministic Area labels.
  - Non-public domains still skip README insertion.
- **Validation**:
  - `scripts/check.sh --tests -- -k tools_skill_management_create_skill`

### Task 1.3: Add the stale-path audit procedure

- **Location**:
  - `docs/plans/skill-folder-migration-plan.md`
  - `docs/runbooks/skills/TOOLING_INDEX_V2.md`
  - `docs/plans/skill-folder-migration-review-source.md`
- **Description**: Define old-path audit commands and move-batch review rules.
- **Dependencies**:
  - Task 1.1
- **Complexity**: 1
- **Acceptance criteria**:
  - Each moved directory has a repeatable old-path audit.
  - Historical references are reviewed deliberately.
  - The audit rule is captured in both the source artifact and execution plan.
- **Validation**:
  - `rg -n "skills/tools/devex" README.md docs skills tests scripts`
  - `rg -n "skills/automation/(gh-fix-ci|release-workflow)" README.md docs skills tests scripts`

## Sprint 2: Tool Folder Migration

**Goal**: Move overloaded tool folders into clearer bounded-tool areas without
changing skill behavior.
**Demo/Validation**:

- Command(s): `scripts/check.sh --contracts --skills-layout`,
  `scripts/check.sh --docs`, `scripts/check.sh --markdown`
- Verify: moved tool skills validate, README links resolve, and old
  current-contract tool paths are gone.

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
- **Description**: Move evidence primitives into `tools/workflow-evidence`.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 5
- **Acceptance criteria**:
  - Evidence capture remains in nils-cli primitives.
  - Skill judgment and policy remain in SKILL.md.
  - Moved skills keep tests and references intact.
  - No old current-contract path remains for the moved evidence skills.
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
- **Description**: Move scope, git, review, and notification helpers out of `tools/devex`.
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
- **Description**: Move browser, agent-doc bootstrap, and app runtime tools into target areas.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 5
- **Acceptance criteria**:
  - Runtime browser tools stay distinct from evidence-recording tools.
  - Agent-doc bootstrap and macOS app runtime move out of flat `skills/tools/`.
  - Browser-related tests and references still resolve.
- **Validation**:
  - `scripts/check.sh --contracts --skills-layout`
  - `scripts/check.sh --tests -- -k "agent_doc_init or macos_agent_ops or browser_session or web_evidence or web_qa or playwright or agent_browser"`

## Sprint 3: Automation Folder Migration

**Goal**: Move flat automation skills into areas that reflect the loop they
own: commit, issue delivery, CI repair, bug work, security scan, and release.
**Demo/Validation**:

- Command(s): `scripts/check.sh --contracts --skills-layout`,
  `scripts/check.sh --docs`, `scripts/check.sh --markdown`
- Verify: automation skills still read as end-to-end loop owners and no old
  current-contract automation path remains.

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
- **Description**: Move commit and issue-delivery automation into target subareas.
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
- **Description**: Move CI, bug, security, and release automation into target subareas.
- **Dependencies**:
  - Task 1.2
  - Task 1.3
- **Complexity**: 5
- **Acceptance criteria**:
  - CI, bug, Semgrep, and release workflows stay under `automation`.
  - `tools` never owns those automation loops.
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
- **Description**: Run old-path audits and update only current-contract references.
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
  - Entrypoint ownership checks pass.
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
- **Description**: Run the full validation gate and fix moved-path breakage.
- **Dependencies**:
  - Task 4.1
- **Complexity**: 3
- **Acceptance criteria**:
  - `scripts/check.sh --all` passes.
  - CI phase mappings change only for intentional moved-path updates.
- **Validation**:
  - `scripts/check.sh --all`

## Testing Strategy

- Unit: run focused pytest selections for moved skill groups after each sprint.
- Integration: run contract/layout checks after each directory move batch.
- Docs: run `scripts/check.sh --docs` and `scripts/check.sh --markdown` after
  each sprint.
- Repository gate: run `scripts/check.sh --all` before reporting the migration
  complete.

## Risks & gotchas

- Moving skill folders can break skill discovery, README links, hook
  allow-lists, and test fixtures even when SKILL.md content is unchanged.
- `create-skill` README insertion is the first dependency to prove before
  moving folders.
- `plan-issue-delivery` and browser skills have many nested references and are
  likely overlap hotspots.
- Blind search-and-replace can corrupt historical docs; review old-path hits
  before editing them.
- Symlinks or duplicate compatibility folders can confuse layout audits and are
  out of scope unless validation proves they are required.

## Rollback plan

- Revert each sprint commit independently if validation fails after that
  sprint.
- If a move batch is partially applied, use `git mv` to restore the old path
  and rerun `scripts/check.sh --contracts --skills-layout`.
- If nested-area tooling changes are valid but a later move is risky, keep
  Sprint 1 and postpone the folder moves.
