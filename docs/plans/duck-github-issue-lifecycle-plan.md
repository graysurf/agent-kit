# Plan: Duck plan for GitHub issue lifecycle testing

## Overview
This plan validates the real `plan-issue` development lifecycle on GitHub using one plan issue across three sprints with intentionally different dependency topologies. All implementation changes in PRs are constrained to `tests/issues/duck-lifecycle/` so cleanup is one-shot and low risk after testing.

## Scope
- In scope:
  - Create disposable lifecycle test fixtures only under `tests/issues/duck-lifecycle/`.
  - Exercise real lifecycle gates on GitHub issue flow (`start-plan`, `start-sprint`, `link-pr`, `ready-sprint`, `accept-sprint`, `ready-plan`, `close-plan`).
  - Validate three sprint topology patterns:
    - Sprint 1: fully serial (no parallelism).
    - Sprint 2: parallel-capable with intra-sprint dependency convergence.
    - Sprint 3: parallel-capable with no intra-sprint dependencies.
- Out of scope:
  - Production feature/code changes outside `tests/issues/`.
  - Permanent documentation updates outside this plan file.
  - CI/release process changes.

## Assumptions
1. `gh auth status` is valid for the target repository.
2. Latest unreleased CLIs are run via wrappers in debug mode:
   - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-tooling`
   - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-issue`
   - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-issue-local`
3. `AGENT_HOME` is set (or defaults to repo root) for writing validation artifacts under `$AGENT_HOME/out/duck-lifecycle/`.
4. Subagent implementation PRs can be opened and merged in the test repository.

## Sprint 1: Fully serial baseline
**Goal**: prove sprint execution is strictly serial and still flows through full lifecycle gates.
**Demo/Validation**:
- Command(s):
  - `AGENT_HOME="${AGENT_HOME:-$PWD}"; OUT_DIR="$AGENT_HOME/out/duck-lifecycle"; mkdir -p "$OUT_DIR"`
  - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-tooling validate --file docs/plans/duck-github-issue-lifecycle-plan.md`
  - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-tooling batches --file docs/plans/duck-github-issue-lifecycle-plan.md --sprint 1 > "$OUT_DIR/s1-batches.json"`
  - `python3 - <<'PY'\nimport json, os\nfrom pathlib import Path\nroot = Path(os.environ.get("AGENT_HOME", "."))\nbatches = json.loads((root / "out/duck-lifecycle/s1-batches.json").read_text())["batches"]\nassert [len(b) for b in batches] == [1, 1, 1], batches\nprint("ok")\nPY`
- Verify:
  - Sprint 1 batch widths are exactly `[1, 1, 1]` (no parallel layer).

### Task 1.1: Bootstrap disposable lifecycle workspace
- **Location**:
  - `tests/issues/duck-lifecycle/README.md`
  - `tests/issues/duck-lifecycle/CLEANUP.md`
- **Description**: Create the disposable root with lifecycle intent, test-only warning, and one-command cleanup guidance.
- **Dependencies**: none
- **Complexity**: 2
- **Acceptance criteria**:
  - README states this area is disposable and PR-safe for lifecycle testing.
  - CLEANUP includes `rm -rf tests/issues/duck-lifecycle`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/README.md && test -f tests/issues/duck-lifecycle/CLEANUP.md`
  - `rg -n 'disposable|lifecycle|tests/issues/duck-lifecycle' tests/issues/duck-lifecycle/README.md`
  - `rg -n 'rm -rf tests/issues/duck-lifecycle' tests/issues/duck-lifecycle/CLEANUP.md`

### Task 1.2: Add serial step A fixture
- **Location**:
  - `tests/issues/duck-lifecycle/sprint1/serial/step-a.md`
- **Description**: Add the first serial fixture artifact for Sprint 1.
- **Dependencies**:
  - Task 1.1
- **Complexity**: 2
- **Acceptance criteria**:
  - File exists and includes `topology: serial`.
  - File includes `step: A`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint1/serial/step-a.md`
  - `rg -n 'topology: serial|step: A' tests/issues/duck-lifecycle/sprint1/serial/step-a.md`

### Task 1.3: Add serial step B fixture
- **Location**:
  - `tests/issues/duck-lifecycle/sprint1/serial/step-b.md`
- **Description**: Add the second serial fixture artifact and mark it as dependent continuation.
- **Dependencies**:
  - Task 1.2
- **Complexity**: 2
- **Acceptance criteria**:
  - File exists and includes `topology: serial`.
  - File includes `depends-on: Task 1.2`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint1/serial/step-b.md`
  - `rg -n 'topology: serial|depends-on: Task 1.2' tests/issues/duck-lifecycle/sprint1/serial/step-b.md`

## Sprint 2: Parallel with dependencies
**Goal**: validate parallel-capable tasks with an explicit dependency convergence gate inside the sprint.
**Demo/Validation**:
- Command(s):
  - `AGENT_HOME="${AGENT_HOME:-$PWD}"; OUT_DIR="$AGENT_HOME/out/duck-lifecycle"; mkdir -p "$OUT_DIR"`
  - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-tooling batches --file docs/plans/duck-github-issue-lifecycle-plan.md --sprint 2 > "$OUT_DIR/s2-batches.json"`
  - `python3 - <<'PY'\nimport json, os\nfrom pathlib import Path\nroot = Path(os.environ.get("AGENT_HOME", "."))\nbatches = json.loads((root / "out/duck-lifecycle/s2-batches.json").read_text())["batches"]\nassert [len(b) for b in batches] == [2, 1], batches\nprint("ok")\nPY`
  - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-issue-local build-task-spec --plan docs/plans/duck-github-issue-lifecycle-plan.md --issue 999 --sprint 2 --pr-grouping group --strategy deterministic --pr-group S2T1=s2-core --pr-group S2T2=s2-core --pr-group S2T3=s2-integration --task-spec-out "$OUT_DIR/s2-task-spec.tsv" --dry-run`
- Verify:
  - Sprint 2 batch widths are exactly `[2, 1]`.
  - Task-spec generation succeeds with deterministic group mapping.

### Task 2.1: Add parallel source fixture A
- **Location**:
  - `tests/issues/duck-lifecycle/sprint2/dependent-parallel/source-a.md`
- **Description**: Create one independent source artifact for Sprint 2 parallel lane setup.
- **Dependencies**: none
- **Complexity**: 2
- **Acceptance criteria**:
  - File exists and includes `topology: dependent-parallel`.
  - File includes `lane: A`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint2/dependent-parallel/source-a.md`
  - `rg -n 'topology: dependent-parallel|lane: A' tests/issues/duck-lifecycle/sprint2/dependent-parallel/source-a.md`

### Task 2.2: Add parallel source fixture B
- **Location**:
  - `tests/issues/duck-lifecycle/sprint2/dependent-parallel/source-b.md`
- **Description**: Create second independent source artifact for Sprint 2 parallel lane setup.
- **Dependencies**: none
- **Complexity**: 2
- **Acceptance criteria**:
  - File exists and includes `topology: dependent-parallel`.
  - File includes `lane: B`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint2/dependent-parallel/source-b.md`
  - `rg -n 'topology: dependent-parallel|lane: B' tests/issues/duck-lifecycle/sprint2/dependent-parallel/source-b.md`

### Task 2.3: Add convergence fixture depending on both lanes
- **Location**:
  - `tests/issues/duck-lifecycle/sprint2/dependent-parallel/converge.md`
- **Description**: Add dependent convergence artifact that can start only after both parallel source tasks complete.
- **Dependencies**:
  - Task 2.1
  - Task 2.2
- **Complexity**: 3
- **Acceptance criteria**:
  - File exists and includes `topology: dependent-parallel`.
  - File includes `depends-on: Task 2.1, Task 2.2`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint2/dependent-parallel/converge.md`
  - `rg -n 'topology: dependent-parallel|depends-on: Task 2.1, Task 2.2' tests/issues/duck-lifecycle/sprint2/dependent-parallel/converge.md`

## Sprint 3: Parallel with no dependencies
**Goal**: validate full intra-sprint parallelism with no task dependency edges.
**Demo/Validation**:
- Command(s):
  - `AGENT_HOME="${AGENT_HOME:-$PWD}"; OUT_DIR="$AGENT_HOME/out/duck-lifecycle"; mkdir -p "$OUT_DIR"`
  - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-tooling batches --file docs/plans/duck-github-issue-lifecycle-plan.md --sprint 3 > "$OUT_DIR/s3-batches.json"`
  - `python3 - <<'PY'\nimport json, os\nfrom pathlib import Path\nroot = Path(os.environ.get("AGENT_HOME", "."))\nbatches = json.loads((root / "out/duck-lifecycle/s3-batches.json").read_text())["batches"]\nassert len(batches) == 1 and len(batches[0]) == 3, batches\nprint("ok")\nPY`
  - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-issue-local build-task-spec --plan docs/plans/duck-github-issue-lifecycle-plan.md --issue 999 --sprint 3 --pr-grouping group --strategy deterministic --pr-group S3T1=s3-a --pr-group S3T2=s3-b --pr-group S3T3=s3-c --task-spec-out "$OUT_DIR/s3-task-spec.tsv" --dry-run`
- Verify:
  - Sprint 3 has one batch containing all 3 tasks.
  - Task-spec generation succeeds with isolated deterministic groups.

### Task 3.1: Add independent parallel fixture A
- **Location**:
  - `tests/issues/duck-lifecycle/sprint3/independent-parallel/task-a.md`
- **Description**: Add first independent task artifact for no-dependency parallel sprint.
- **Dependencies**: none
- **Complexity**: 2
- **Acceptance criteria**:
  - File exists and includes `topology: independent-parallel`.
  - File includes `lane: A`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint3/independent-parallel/task-a.md`
  - `rg -n 'topology: independent-parallel|lane: A' tests/issues/duck-lifecycle/sprint3/independent-parallel/task-a.md`

### Task 3.2: Add independent parallel fixture B
- **Location**:
  - `tests/issues/duck-lifecycle/sprint3/independent-parallel/task-b.md`
- **Description**: Add second independent task artifact for no-dependency parallel sprint.
- **Dependencies**: none
- **Complexity**: 2
- **Acceptance criteria**:
  - File exists and includes `topology: independent-parallel`.
  - File includes `lane: B`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint3/independent-parallel/task-b.md`
  - `rg -n 'topology: independent-parallel|lane: B' tests/issues/duck-lifecycle/sprint3/independent-parallel/task-b.md`

### Task 3.3: Add independent parallel fixture C
- **Location**:
  - `tests/issues/duck-lifecycle/sprint3/independent-parallel/task-c.md`
- **Description**: Add third independent task artifact for no-dependency parallel sprint.
- **Dependencies**: none
- **Complexity**: 2
- **Acceptance criteria**:
  - File exists and includes `topology: independent-parallel`.
  - File includes `lane: C`.
- **Validation**:
  - `test -f tests/issues/duck-lifecycle/sprint3/independent-parallel/task-c.md`
  - `rg -n 'topology: independent-parallel|lane: C' tests/issues/duck-lifecycle/sprint3/independent-parallel/task-c.md`

## Testing Strategy
- Unit:
  - Not applicable (test fixture and orchestration plan only).
- Integration:
  - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-tooling validate --file docs/plans/duck-github-issue-lifecycle-plan.md`
  - Validate sprint dependency topology via `plan-tooling batches` for S1/S2/S3.
  - Validate deterministic grouping execution via `plan-issue-local build-task-spec` for S2/S3.
- E2E/manual (real GitHub issue lifecycle):
  - Set context:
    - `REPO_SLUG="<owner/repo>"`
    - `PLAN_FILE="docs/plans/duck-github-issue-lifecycle-plan.md"`
  - Start one plan issue (`1 plan = 1 issue`):
    - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-issue start-plan --repo "$REPO_SLUG" --plan "$PLAN_FILE" --pr-grouping group --strategy deterministic --pr-group S1T1=s1-serial --pr-group S1T2=s1-serial --pr-group S1T3=s1-serial --pr-group S2T1=s2-core --pr-group S2T2=s2-core --pr-group S2T3=s2-integration --pr-group S3T1=s3-a --pr-group S3T2=s3-b --pr-group S3T3=s3-c`
  - For each sprint (`start-sprint -> link-pr -> ready-sprint -> merge -> accept-sprint`):
    - Sprint 1 links one lane PR with `--sprint 1 --pr-group s1-serial`.
    - Sprint 2 links two PR lanes (`s2-core`, `s2-integration`).
    - Sprint 3 links three isolated PRs (task-scoped `S3T1/S3T2/S3T3` or group-scoped `s3-a/s3-b/s3-c`).
  - Enforce PR change boundary on every PR before merge:
    - `git diff --name-only origin/main...HEAD | rg -v '^tests/issues/' && { echo 'unexpected file touched'; exit 1; } || true`
  - Finalize lifecycle:
    - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-issue ready-plan --repo "$REPO_SLUG" --issue "$ISSUE_NUM"`
    - `NILS_WRAPPER_MODE=debug /Users/terry/Project/graysurf/nils-cli/wrappers/plan-issue close-plan --repo "$REPO_SLUG" --issue "$ISSUE_NUM" --approved-comment-url "$FINAL_APPROVAL_URL"`

## Risks & gotchas
- `group + deterministic` requires complete `--pr-group` mapping coverage; missing any task fails validation.
- `link-pr --sprint <n>` becomes ambiguous if multiple runtime lanes exist and `--pr-group` is omitted.
- Real GitHub run requires valid approval comment URLs for `accept-sprint` and `close-plan`.
- If any PR touches files outside `tests/issues/`, cleanup scope expands and defeats disposable-test intent.
- Closing flow enforces merged PR and worktree cleanup gates; partial lifecycle runs are not considered done.

## Rollback plan
- If any sprint test is invalid, close open PRs and stop at current sprint without advancing.
- If plan-level execution must be aborted, close the plan issue with explicit rationale and leave audit comments.
- Remove disposable fixtures in one step:
  - `rm -rf tests/issues/duck-lifecycle`
