# Agent-kit Skill Adoption Architecture For nils-cli Primitives

Status: active; first adoption and workflow-consumption slices landed
Date: 2026-05-17
Scope: agent-kit skill layout and adoption path for `nils-cli` commands

## Purpose

Define how agent-kit should organize skills around `nils-cli` primitives,
starting with implemented command contracts and thin tool skills.

This document is a landing architecture record. It is not an implementation
plan, and it should not be used to claim that any candidate `nils-cli` command
exists before the command surface is implemented.

## Context

Source facts:

- agent-kit already treats `nils-cli` as the stable provider for shared CLI
  primitives such as `agent-docs`, `plan-issue`, `plan-tooling`, `api-*`,
  `semantic-commit`, `agent-out`, `screen-record`, and `image-processing`.
- Existing skill docs distinguish CLI-backed tool skills from workflow skills:
  tool skills expose deterministic entrypoints, while workflow and automation
  skills decide when and how to use them.
- Candidate and landed `nils-cli` primitives are tracked in
  `docs/runbooks/nils-cli/skill-consumable-primitives.md`.
- `agent-scope-lock` is implemented in the nils-cli repository with
  `create`, `read`, `validate`, `clear`, and `completion` subcommands.
- `web-evidence` is implemented in the nils-cli repository with `capture` and
  `completion` subcommands for redacted static HTTP evidence bundles.
- agent-kit now consumes `web-evidence` from release and issue-follow-up
  workflows when static HTTP/HTTPS evidence is enough.
- agent-kit now has a Codex hook guard that validates active
  `agent-scope-lock` scopes and reports concise violations.
- `nils-cli` now has the `nils-agent-workflow-primitives` package with
  `browser-session`, `canary-check`, `docs-impact`, `model-cross-check`, and
  `review-evidence` binaries.
- agent-kit now has thin tool skills for those five binaries. They document
  released PATH expectations, verified local PATH usage on this machine, and
  validated local-checkout fallback usage before distributable release adoption.

Assumptions:

- agent-kit should wait for a concrete nils-cli command contract before adding
  canonical skill entries for any later primitive.
- agent-kit can still prepare folder boundaries, migration rules, and adoption
  criteria now.
- Existing skills should remain valid while nils-cli primitives are under
  development.

Inference:

- The safest landing path is adapter-first: add or update thin tool skills only
  after nils-cli provides stable help, JSON or text output, failure behavior,
  and version floor. Then update workflow skills to consume those tool skills.

## Current Judgment

Organize nils-cli skill consumption in three layers:

1. Tool contract layer: one tool skill per stable nils-cli primitive when the
   primitive has standalone user value or repeated workflow consumption.
2. Workflow consumption layer: existing workflows call the tool skill or direct
   nils-cli command, but keep user-facing judgment and escalation in the
   workflow skill.
3. Automation integration layer: automation skills adopt the command only after
   failure modes are stable enough for unattended runs.

First adoption slices:

- `skills/tools/devex/agent-scope-lock/` is the reusable tool skill for the
  implemented edit-scope lock primitive.
- `skills/tools/browser/web-evidence/` is the reusable tool skill for the
  implemented static HTTP evidence primitive.
- Both are intentionally scriptless: skills and agents call the nils-cli
  command surfaces directly instead of reimplementing lock storage, validation,
  HTTP fetching, redaction, schema generation, or artifact naming.
- They document both the released PATH boundary and the local checkout fallback
  boundary.
- First workflow consumers landed for static URL evidence and test-first
  evidence fields. `test-first-evidence` now also has a tool skill contract for
  the implemented nils-cli command.
- `browser-session`, `canary-check`, `docs-impact`, `model-cross-check`, and
  `review-evidence` now have tool skill contracts for the implemented
  `nils-agent-workflow-primitives` binaries. Their first slice is deterministic
  evidence capture or Git change scanning; active browser automation, provider
  model calls, and deploy orchestration stay in higher-level workflows.

Do not create broad gstack-style specialist skills as part of this landing
architecture. The first value is reusable evidence, guardrails, and validation,
not new product-review personas.

## Proposed Skill Mapping

| nils-cli primitive | First agent-kit landing | Later consumers | Notes |
| --- | --- | --- | --- |
| `web-evidence` | Landed: `skills/tools/browser/web-evidence/`. | Landed: `release-workflow`, `issue-follow-up`; later: future `web-qa`, `gh-fix-ci` | First slice is static HTTP evidence; use browser tooling when JavaScript, screenshots, cookies, auth state, or console logs are required. |
| `browser-session` | Landed: `skills/tools/browser/browser-session/`. | `web-evidence`, future `web-qa`, `screenshot`, possible `agent-browser` replacement | First slice records session evidence; it does not replace Browser, Chrome, or Playwright automation. |
| `agent-scope-lock` | Landed: `skills/tools/devex/agent-scope-lock/`. | Landed: Codex hook guard; later: `gh-fix-ci`, `find-and-fix-bugs`, `plan-issue-delivery` | Hook guard validates active locks and reports violations; workflow consumption should stay opt-in until unattended failure modes are proven. |
| `docs-impact` | Landed: `skills/tools/devex/docs-impact/`. | `release-workflow`, `docs-plan-cleanup`, future document-release equivalent | Reports docs/non-doc changed files and review hints; rewriting docs remains a skill decision. |
| `review-evidence` | Landed: `skills/tools/devex/review-evidence/`. | `review-to-improvement-doc`, `issue-pr-review`, PR workflows | Normalizes findings without replacing code-review judgment. |
| `test-first-evidence` | Landed: `skills/tools/devex/test-first-evidence/`. | Landed: `find-and-fix-bugs`, `fix-bug-pr`, `gh-fix-ci`, `issue-subagent-pr`, `execute-plan-parallel`, PR/MR creation workflows | Skills decide whether test-first applies; the CLI records failing evidence, waiver, final validation, redaction, and completeness checks. |
| `canary-check` | Landed: `skills/tools/devex/canary-check/`. | `release-workflow`, future `land-and-deploy`, future `web-qa` | Runs one caller-owned local command and records redacted pass/fail evidence; it is not a deploy orchestrator. |
| `model-cross-check` | Landed: `skills/tools/devex/model-cross-check/`. | PR review workflows, research workflows | Records observations only; provider auth, cost, and routing remain outside the CLI. |

## Adoption Criteria

Before adding a new agent-kit tool skill for a nils-cli primitive:

- The nils-cli command exists on `PATH` in a released or locally documented
  version.
- `--help` or equivalent command documentation is stable enough to cite.
- Output format is stable enough for skill instructions to reference.
- Failure modes are documented with exit codes or machine-readable error fields.
- Artifact paths are deterministic and compatible with `agent-out` conventions.
- Secret and redaction behavior is clear.
- A fallback or blocked-state response is defined when nils-cli is too old or
  the command is unavailable.

Before updating workflow or automation skills to consume it:

- The tool skill or command contract is validated by tests.
- The workflow can distinguish tool failure from product/runtime failure.
- The workflow does not duplicate low-level CLI behavior in prose.
- Any unattended automation has a safe fail-closed path.

## Skill Layout Rules

- Put browser and web evidence primitives under `skills/tools/browser/`.
- Put edit-scope, docs-impact, review-evidence, canary-check, and
  model-cross-check primitives under `skills/tools/devex/` unless a clearer
  existing category emerges.
- Put release/canary orchestration in existing automation or release workflow
  skills; do not create a parallel release stack.
- Keep project or company-specific adoption under `skills/_projects/` until the
  command proves generally useful.
- Update `docs/runbooks/skills/TOOLING_INDEX_V2.md` only after an entrypoint is
  implemented and tested.
- Update `README.md` only when the skill becomes part of the public catalog.

## Migration Candidates

| Existing skill | Possible future change | Guardrail |
| --- | --- | --- |
| `skills/tools/browser/agent-browser/` | Keep as legacy fallback or mark migration path to nils-cli browser tooling. | Do not remove until new browser command covers refs, state, artifacts, and cleanup. |
| `skills/tools/browser/playwright/` | Keep as direct Playwright wrapper for exploratory or framework-specific cases. | Do not force all browser use through nils-cli if Playwright CLI remains the better fit. |
| `skills/tools/media/screenshot/` | Optionally consume `web-evidence` for URL screenshots only. | Keep generic desktop/window screenshot behavior separate. |
| `skills/automation/release-workflow/` | Consume `web-evidence`, `docs-impact`, or `canary-check` after command contracts are stable. | Keep release guide and project-defined commands as source of truth. |
| `skills/automation/gh-fix-ci/` | Consume `agent-scope-lock` or `web-evidence` only when it improves unattended safety. | Avoid broadening auto-fix scope without mechanical enforcement. |
| `skills/workflows/conversation/review-to-improvement-doc/` | Optionally consume `review-evidence` for normalized finding tables. | Durable docs remain human-readable and source-grounded. |

## Backlog

| Priority | Work item | Acceptance |
| --- | --- | --- |
| P1 | Watch each new nils-cli primitive shape and choose the matching agent-kit landing area. | First set landed: Browser owns `web-evidence` and `browser-session`; DevEx owns `agent-scope-lock`, `test-first-evidence`, `docs-impact`, `review-evidence`, `canary-check`, and `model-cross-check`. |
| P1 | Add a tool skill only after command contract exists. | Skill has contract, prerequisites, failure modes, usage, guardrails, tests, and catalog update if public. |
| P1 | Define too-old nils-cli behavior for each consuming skill. | Done for landed tool skills: they document the released PATH boundary, local checkout fallback, and blocked/degraded behavior. |
| P2 | Add workflow integration after the tool skill is stable. | First integrations landed for `web-evidence` and `agent-scope-lock`; future integrations should reference tool contracts and keep decision logic out of the tool. |
| P2 | Revisit legacy browser wrappers after browser primitive lands. | Migration note documents keep/replace decision with evidence. |

## Validation Gate

For a tool skill that wraps a new nils-cli primitive:

- `scripts/check.sh --docs`
- `scripts/check.sh --markdown`
- `scripts/check.sh --tests -- -k <new-skill-name>`
- `scripts/check.sh --entrypoint-ownership` when new scripts are added.
- `bash scripts/ci/stale-skill-scripts-audit.sh --check` when skill scripts are
  added, removed, or reclassified.

For docs-only adoption records:

- `scripts/check.sh --docs`
- `scripts/check.sh --markdown`
- Direct markdown lint for newly added untracked docs when needed.

## Do Not Do

- Do not create placeholder skills for commands that nils-cli has not shipped.
- Do not add unimplemented candidate commands to the public README skill catalog
  or the canonical tooling index.
- Do not copy nils-cli implementation details into skill prose.
- Do not make workflow skills parse unstable output with ad hoc shell logic.
- Do not make browser evidence, cookies, auth state, or network logs persist
  without explicit redaction and artifact rules.
- Do not introduce a second release/delivery workflow when existing
  provider-scoped GitHub/GitLab skills already own that boundary.

## Open Questions

- For future primitives, should agent-kit continue to expose one tool skill per
  nils-cli binary, or group skills only when nils-cli itself ships a stable
  grouped command?
- Which workflow should consume `agent-scope-lock` after the hook guard proves
  stable in real use?
- Should `browser-session` remain a lower-level record-only complement to
  Browser, Chrome, Playwright, and `web-evidence`, or grow a separate active
  browser automation slice?
