# Plan: Globalize docs plan cleanup skill

## Overview

This plan migrates the project-local `nils-cli-docs-plan-cleanup` skill into a tracked global skill under `skills/workflows/plan/`.
The globalized skill will keep the current dry-run-first cleanup behavior, but use `$PROJECT_PATH` as the default target for deciding which docs files can be deleted.
The migration also includes test coverage and README catalog updates so the skill is discoverable and safe to use across repositories.

## Scope

- In scope:
  - Add a new global planning skill directory with `SKILL.md`, script entrypoint, and tests.
  - Port cleanup logic from `/Users/terry/Project/graysurf/nils-cli/.agents/skills/nils-cli-docs-plan-cleanup/`.
  - Make `$PROJECT_PATH` the default target path, with `--project-path` as an explicit override.
  - Update repository README skill listings for the new global skill.
- Out of scope:
  - Auto-removing the original project-local skill from `nils-cli`.
  - Changing cleanup semantics beyond path-resolution and global-skill packaging.

## Assumptions

1. The global skill name will be `docs-plan-cleanup`, and it belongs to `workflows/plan`.
2. `$PROJECT_PATH` points to the intended target project root (or a subdirectory inside that git work tree).
3. Existing report sections (for example `docs-plan-cleanup-report:v1`) remain stable to avoid breaking downstream workflows.

## Sprint 1: Global skill scaffold and behavior port

**Goal**: create a tracked global plan skill and port the cleanup script with neutral naming.
**Demo/Validation**:
- Command(s):
  - `bash skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh --help`
  - `bash skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh --file skills/workflows/plan/docs-plan-cleanup/SKILL.md`
- Verify:
  - The new skill contract is valid and script entrypoint is runnable.

### Task 1.1: Scaffold the global skill directory and contract
- **Location**:
  - `skills/workflows/plan/docs-plan-cleanup/SKILL.md`
  - `skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh`
  - `skills/workflows/plan/docs-plan-cleanup/tests/test_workflows_plan_docs_plan_cleanup.py`
- **Description**: Create the new tracked skill directory and baseline files. Write `SKILL.md` in global-skill format with absolute `$AGENT_HOME` script paths, classify it as a plan workflow skill, and define dry-run-first usage.
- **Dependencies**: none
- **Acceptance criteria**:
  - The new skill directory exists with required top-level entries for tracked skills.
  - `SKILL.md` contract sections pass `validate_skill_contracts.sh`.
  - The documented script entrypoint uses `$AGENT_HOME/skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh`.
- **Validation**:
  - `test -f skills/workflows/plan/docs-plan-cleanup/SKILL.md`
  - `test -f skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh`
  - `bash skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh --file skills/workflows/plan/docs-plan-cleanup/SKILL.md`

### Task 1.2: Port cleanup logic from the project-local script
- **Location**:
  - `skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh`
- **Description**: Port the local script logic into the global script, removing project-specific naming while preserving keep-plan resolution, related-doc classification, and deterministic report output.
- **Dependencies**:
  - Task 1.1
- **Acceptance criteria**:
  - The global script preserves dry-run and execute modes.
  - The report still emits the same section contract (`plan_md_to_clean`, `plan_related_md_to_clean`, retained/rehome/manual-review sections, and execution status).
  - `--keep-plan`, `--keep-plans-file`, `--delete-important`, and `--delete-empty-dirs` behave consistently with the source skill.
- **Validation**:
  - `rg -n "docs-plan-cleanup-report:v1" skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh`
  - `bash skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh --help`

### Task 1.3: Make `$PROJECT_PATH` the default target resolver
- **Location**:
  - `skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh`
  - `skills/workflows/plan/docs-plan-cleanup/SKILL.md`
- **Description**: Update target-path resolution so the script defaults to `$PROJECT_PATH` when present, falls back to current directory when absent, and still allows explicit `--project-path` override. Document precedence clearly in the skill contract and usage examples.
- **Dependencies**:
  - Task 1.2
- **Acceptance criteria**:
  - Without `--project-path`, the script targets `$PROJECT_PATH` if exported.
  - `--project-path` overrides `$PROJECT_PATH`.
  - Invalid or non-git target paths return actionable errors.
- **Validation**:
  - `tmp="$(mktemp -d)" && git -C "$tmp" init >/dev/null && mkdir -p "$tmp/docs/plans" && printf '# keep\n' > "$tmp/docs/plans/keep-plan.md" && PROJECT_PATH="$tmp" bash skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh --keep-plan keep-plan >/dev/null`
  - `PROJECT_PATH="/path/that/does/not/exist" bash skills/workflows/plan/docs-plan-cleanup/scripts/docs-plan-cleanup.sh --project-path "$(pwd)" --help >/dev/null`

## Sprint 2: Tests and safety checks

**Goal**: verify behavior parity and path-resolution safety through automated tests.
**Demo/Validation**:
- Command(s):
  - `bash skills/workflows/plan/docs-plan-cleanup/tests/test_docs_plan_cleanup.sh`
  - `pytest -q skills/workflows/plan/docs-plan-cleanup/tests/test_workflows_plan_docs_plan_cleanup.py`
- Verify:
  - Dry-run/execute behavior and contract/entrypoint checks both pass.

### Task 2.1: Port integration behavior test for cleanup actions
- **Location**:
  - `skills/workflows/plan/docs-plan-cleanup/tests/test_docs_plan_cleanup.sh`
- **Description**: Port and adapt the existing shell integration test from the local skill so it validates dry-run report sections, execution deletions, retained docs behavior, and `--delete-important` semantics in temporary git repos.
- **Dependencies**:
  - Task 1.3
- **Acceptance criteria**:
  - Test creates isolated temporary repos and checks expected file deletion/retention outcomes.
  - Test asserts report sections and counts for dry-run mode.
  - Test exits non-zero on any regression in cleanup behavior.
- **Validation**:
  - `bash skills/workflows/plan/docs-plan-cleanup/tests/test_docs_plan_cleanup.sh`

### Task 2.2: Add pytest skill smoke tests for contract and entrypoint
- **Location**:
  - `skills/workflows/plan/docs-plan-cleanup/tests/test_workflows_plan_docs_plan_cleanup.py`
- **Description**: Add standard repo skill smoke tests using `assert_skill_contract` and `assert_entrypoints_exist` so the new skill is covered by existing testing conventions.
- **Dependencies**:
  - Task 1.1
- **Acceptance criteria**:
  - The test verifies contract validity for `SKILL.md`.
  - The test verifies `scripts/docs-plan-cleanup.sh` exists as the declared entrypoint.
  - The test file follows naming and helper usage patterns used by other tracked skills.
- **Validation**:
  - `pytest -q skills/workflows/plan/docs-plan-cleanup/tests/test_workflows_plan_docs_plan_cleanup.py`

### Task 2.3: Run governance checks on the new tracked skill layout
- **Location**:
  - `skills/workflows/plan/docs-plan-cleanup/SKILL.md`
  - `skills/workflows/plan/docs-plan-cleanup/tests/test_workflows_plan_docs_plan_cleanup.py`
  - `skills/workflows/plan/docs-plan-cleanup/tests/test_docs_plan_cleanup.sh`
- **Description**: Run skill-governance layout and contract checks against the new skill directory and ensure the test suite used by this skill is green before documentation updates are finalized.
- **Dependencies**:
  - Task 2.1
  - Task 2.2
- **Acceptance criteria**:
  - `audit-skill-layout` passes for this skill directory.
  - Contract validation and both test commands pass.
  - No unexpected top-level entries exist in the new skill directory.
- **Validation**:
  - `bash skills/tools/skill-management/skill-governance/scripts/audit-skill-layout.sh --skill-dir skills/workflows/plan/docs-plan-cleanup`
  - `bash skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh --file skills/workflows/plan/docs-plan-cleanup/SKILL.md`
  - `bash skills/workflows/plan/docs-plan-cleanup/tests/test_docs_plan_cleanup.sh`
  - `pytest -q skills/workflows/plan/docs-plan-cleanup/tests/test_workflows_plan_docs_plan_cleanup.py`

## Sprint 3: README updates and rollout guidance

**Goal**: make the skill discoverable and document correct `$PROJECT_PATH` usage.
**Demo/Validation**:
- Command(s):
  - `rg -n "docs-plan-cleanup" README.md`
  - `rg -n "PROJECT_PATH|--project-path" skills/workflows/plan/docs-plan-cleanup/SKILL.md`
- Verify:
  - README references and usage guidance are complete and consistent.

### Task 3.1: Add the skill to the top-level README skill catalog
- **Location**:
  - `README.md`
- **Description**: Update the `## 🛠️ Skills` section to include `docs-plan-cleanup` in the Planning area with a concise description that highlights safe docs/plans cleanup and global usage.
- **Dependencies**:
  - Task 1.1
- **Acceptance criteria**:
  - README contains a new Planning-row link to `./skills/workflows/plan/docs-plan-cleanup/`.
  - Description clearly states it is dry-run-first and targets project docs cleanup.
  - Table formatting remains valid markdown and visually aligned with adjacent rows.
- **Validation**:
  - `rg -n "\\[docs-plan-cleanup\\]\\(\\./skills/workflows/plan/docs-plan-cleanup/\\)" README.md`

### Task 3.2: Document `$PROJECT_PATH` behavior and override examples in SKILL.md
- **Location**:
  - `skills/workflows/plan/docs-plan-cleanup/SKILL.md`
- **Description**: Expand usage docs to show default target selection from `$PROJECT_PATH`, explicit override with `--project-path`, and a recommended review-before-`--execute` workflow.
- **Dependencies**:
  - Task 1.3
- **Acceptance criteria**:
  - SKILL docs include at least one command using `$PROJECT_PATH` implicitly.
  - SKILL docs include at least one command with explicit `--project-path`.
  - Safety guidance still requires dry-run review before applying deletions.
- **Validation**:
  - `rg -n "PROJECT_PATH|--project-path|--execute" skills/workflows/plan/docs-plan-cleanup/SKILL.md`

## Testing Strategy

- Unit:
  - Pytest smoke checks for skill contract and entrypoint presence.
- Integration:
  - Shell integration test for end-to-end dry-run and execute cleanup behavior on temporary git repos.
- Manual:
  - One manual dry-run against a sample project to verify report readability and deletion candidate lists before any real `--execute`.

## Risks & gotchas

- Incorrect target resolution could delete docs in the wrong repository if `$PROJECT_PATH` is stale; script and docs must clearly define precedence and print resolved project path.
- Related-doc detection is reference-based and may miss implicit dependencies; keep dry-run review mandatory.
- Important docs (`docs/specs/**`, `docs/runbooks/**`) need conservative defaults to avoid accidental policy loss.
- Naming drift between local and global scripts can break existing automation; if needed, document migration aliases explicitly.

## Rollback plan

- Revert the new global skill directory (`skills/workflows/plan/docs-plan-cleanup/`) and README row changes.
- Keep the project-local skill as the active fallback while global packaging is corrected.
- Re-run governance and tests after rollback to confirm repo integrity.
