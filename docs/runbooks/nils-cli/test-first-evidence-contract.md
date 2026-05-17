# Test-First Evidence Contract Improvement Record

Status: active; workflow contract landed, nils-cli primitive pending
Date: 2026-05-17
Scope: agent-kit skill behavior and future `nils-cli` evidence support

## Purpose

Preserve the practical conclusions for adding a test-first development contract
to agent-kit without turning it into a brittle global rule.

This record is not an implementation plan. It defines the expected behavior,
landing layers, evidence shape, and guardrails that a later implementation
session should treat as read-first context.

## Context

Source facts:

- A reusable tracked prompt-style skill exists at `skills/workflows/prompts/test-first/`.
- agent-kit favors stable CLI primitives for deterministic behavior while
  leaving workflow judgment in skills.
- Existing nils-cli adoption records keep candidate commands separate from
  implemented entrypoints.
- GitHub and GitLab delivery workflows are provider-scoped audited boundaries,
  so PR/MR creation skills should keep that role instead of becoming generic
  implementation gatekeepers.
- Behavior-editing workflows now carry a `Test-First Evidence Gate`.
- GitHub PR and GitLab MR body templates now surface `Test-First Evidence`.

Assumptions:

- The final `nils-cli` command name and output schema are not decided yet.
- The first implementation can start in skills and PR/MR templates before a
  nils-cli primitive exists.
- Repositories vary in test maturity, so a hard unwaivable rule would create
  false failures in valid docs-only, config-only, generated, visual, or no-test
  harness tasks.

Inference:

- The right agent-kit contract is "failing-test evidence or explicit waiver
  before production code", not "always block every production edit without a
  failing test".

## Current Judgment

Add a default test-first evidence contract:

> For testable production behavior changes, the agent should add or identify a
> focused failing test before editing production code, capture failing evidence,
> then implement and validate the fix. If test-first is not practical, the agent
> must state a waiver reason and substitute validation before editing production
> code.

This is now an agent-kit workflow contract, not only a prompt habit. The prompt
is useful for immediate opt-in, implementation skills own the waiver decision,
PR/MR templates surface evidence fields, and later a nils-cli evidence primitive
can normalize records.

## Applicability

| Change type | Default expectation | Waiver likely? |
| --- | --- | --- |
| Bug fix | Add or point to a failing regression test first. | Rare. |
| Parser, state machine, API contract, workflow logic | Add a focused unit, integration, or contract test first. | Rare. |
| New feature | Add a failing acceptance/spec test before production code. | Sometimes, if no harness exists yet. |
| Refactor | Prefer characterization or existing protection tests before edits. | Common when behavior is unchanged. |
| Docs-only, formatting-only, generated-only | No failing test required; run docs or generation checks. | Yes. |
| Visual-only polish | Use screenshot or browser evidence instead of a failing unit test. | Common. |
| Emergency hotfix or no usable test harness | Waiver plus smallest meaningful substitute validation. | Yes, but must be explicit. |

## Landing Layers

1. Prompt layer: `skills/workflows/prompts/test-first/references/prompts/test-first.md`
   gives the user an immediate opt-in prompt through the `test-first` skill.
2. Policy layer: `AGENTS.md` carries the concise default expectation, but not
   the full checklist.
3. Implementation workflow layer: behavior-editing skills own the test-first
   decision and waiver path.
4. PR/MR creation layer: create skills display evidence or waiver in the body;
   they do not retroactively enforce the whole development process.
5. CLI primitive layer: future nils-cli support should capture evidence,
   normalize waiver records, and verify final pass results.
6. Hook layer: optional later soft warning or fail-closed checks can be added
   only after the evidence shape is stable.

## Skill Impact

Implementation and automation skills should require failing-test evidence or an
explicit waiver before production edits:

- `skills/automation/find-and-fix-bugs/`
- `skills/automation/fix-bug-pr/`
- `skills/automation/gh-fix-ci/`
- `skills/workflows/issue/issue-subagent-pr/`
- `skills/automation/plan-issue-delivery/`
- `skills/workflows/plan/execute-plan-parallel/`

PR/MR creation skills should require the final body to include evidence fields:

- `skills/workflows/pr/github/create-github-pr/`
- `skills/workflows/mr/gitlab/create-gitlab-mr/`

Recommended PR/MR body fields:

- `Change classification`
- `Failing test before fix`
- `Final validation`
- `Waiver reason`, when applicable

## Future nils-cli Primitive

Working name: `test-first-evidence`.

The command should not decide whether a change is semantically testable. Skills
own that judgment. The CLI should own recording and validating evidence.

Minimum candidate capabilities:

- Start or append an evidence record for the current repo/task.
- Record failing-test evidence: command, exit code, test path or test name,
  concise failure summary, cwd, and artifact path if available.
- Record waiver evidence: reason, affected scope, why a failing test is not
  practical, and substitute validation.
- Record final validation: command, exit code, pass/fail status, and summary.
- Emit deterministic JSON for skills and PR/MR body renderers.
- Store artifacts in a canonical `agent-out` run directory unless an explicit
  output path is provided.

Suggested record fields:

- `status`
- `version`
- `classification`
- `before_evidence`
- `waiver`
- `after_validation`
- `production_paths`
- `test_paths`
- `artifacts`
- `errors`

## Backlog

| Priority | Work item | Acceptance |
| --- | --- | --- |
| P1 | Add the prompt for immediate user opt-in. | Done: `skills/workflows/prompts/test-first/` exists and describes failing evidence, waiver, and final validation. |
| P1 | Update behavior-editing workflow skills. | Done: behavior-editing skills tell agents to capture failing evidence or waiver before production edits. |
| P1 | Update create PR/MR body contracts. | Done: PR/MR bodies include test-first evidence or explicit waiver when production behavior changed. |
| P2 | Prototype nils-cli evidence capture. | Command emits deterministic JSON and stores evidence under `agent-out`. |
| P2 | Add skill consumption after nils-cli stabilizes. | Skills call the CLI instead of hand-formatting evidence records. |
| P3 | Consider hook support. | Hook only warns or fails after evidence fields and waiver behavior are stable. |

## Validation Gate

For prompt/docs-only changes:

- `scripts/check.sh --docs`
- `scripts/check.sh --markdown`
- Direct markdown lint for newly added untracked files when needed.

For future skill changes:

- Run the relevant skill governance checks.
- Run focused tests for changed renderers, scripts, hooks, or PR/MR body
  templates.
- Verify a docs-only waiver path and a behavior-change evidence path.

For future nils-cli changes:

- Help text documents the command contract and examples.
- JSON output has fixture tests.
- Failure modes include invalid command, failing-test record, waiver record, and
  final-pass record tests.
- Agent-kit consuming skills can distinguish CLI failure from product/test
  failure.

## Do Not Do

- Do not add an unwaivable global rule that blocks every production file edit.
- Do not require failing tests for docs-only, formatting-only, generated-only,
  or purely visual tasks.
- Do not make PR/MR creation skills the source of truth for whether test-first
  happened; they should surface evidence.
- Do not let agents weaken, skip, or overfit tests to satisfy the rule.
- Do not add hook fail-closed behavior before the evidence schema and waiver
  path are stable.
- Do not list a nils-cli command in the canonical tooling index before it
  exists and is tested.

## Open Questions

- Should the eventual nils-cli command be named `test-first-evidence`, or should
  it be a subcommand under a broader evidence tool?
- What exact PR/MR body field names should be shared between GitHub and GitLab
  without weakening provider-specific workflow boundaries?
- Should hooks begin as warnings only, or stay out of scope until nils-cli
  evidence capture is implemented?
