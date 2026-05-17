# Agent-kit Skill Adoption Architecture For nils-cli Primitives

Status: active; first adoption slices landed
Date: 2026-05-17
Scope: agent-kit skill layout and adoption path for `nils-cli` commands

## Purpose

Define how agent-kit should organize skills around `nils-cli` primitives,
starting with the implemented `agent-scope-lock` and `web-evidence` commands
while preserving the same adoption criteria for future primitives.

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
- Candidate `nils-cli` primitives are tracked in
  `docs/runbooks/nils-cli/skill-consumable-primitives.md`.
- `agent-scope-lock` is implemented in the nils-cli repository with
  `create`, `read`, `validate`, `clear`, and `completion` subcommands.
- `web-evidence` is implemented in the nils-cli repository with `capture` and
  `completion` subcommands for redacted static HTTP evidence bundles.

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
- They document both the released PATH boundary and the pre-release local
  checkout boundary.

Do not create broad gstack-style specialist skills as part of this landing
architecture. The first value is reusable evidence, guardrails, and validation,
not new product-review personas.

## Proposed Skill Mapping

| nils-cli primitive | First agent-kit landing | Later consumers | Notes |
| --- | --- | --- | --- |
| `web-evidence` | Landed: `skills/tools/browser/web-evidence/`. | `release-workflow`, future `web-qa`, `issue-follow-up`, `gh-fix-ci` | First slice is static HTTP evidence; use browser tooling when JavaScript, screenshots, cookies, auth state, or console logs are required. |
| `browser-session` | New `skills/tools/browser/browser-session/` only if nils-cli owns persistent browser lifecycle. | `web-evidence`, future `web-qa`, `screenshot`, possible `agent-browser` replacement | Keep `agent-browser` explicitly legacy until migration is proven. |
| `agent-scope-lock` | Landed: `skills/tools/devex/agent-scope-lock/`. | `gh-fix-ci`, `find-and-fix-bugs`, `plan-issue-delivery`, Codex hooks | Start as manual validation before hook fail-closed behavior. |
| `docs-impact` | New `skills/tools/devex/docs-impact/` only after output is stable enough for docs workflows. | `release-workflow`, `docs-plan-cleanup`, future document-release equivalent | It should report likely stale docs; rewriting docs remains a skill decision. |
| `review-evidence` | Prefer updating existing review/conversation workflows first; add a tool skill only if users will invoke it directly. | `review-to-improvement-doc`, `issue-pr-review`, PR workflows | Normalize findings without replacing code-review judgment. |
| `test-first-evidence` | Prefer updating behavior-editing workflows first; add a tool skill only after nils-cli can record evidence and waivers. | `find-and-fix-bugs`, `fix-bug-pr`, `gh-fix-ci`, `issue-subagent-pr`, PR/MR creation workflows | Skills decide whether test-first applies; the CLI should record failing evidence, waiver, and final validation. |
| `canary-check` | New automation-facing tool or release reference after deploy targets are configurable. | `release-workflow`, future `land-and-deploy`, future `web-qa` | Must stay read-only and evidence-first before it becomes a deploy gate. |
| `model-cross-check` | Defer. | PR review workflows, research workflows | Needs careful auth, cost, provider, and redaction boundaries. |

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
- Put edit-scope, docs-impact, and review-evidence primitives under
  `skills/tools/devex/` unless a clearer existing category emerges.
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
| P1 | Watch each new nils-cli primitive shape and choose the matching agent-kit landing area. | `agent-scope-lock` landed under DevEx and `web-evidence` landed under Browser based on actual command help/source. |
| P1 | Add a tool skill only after command contract exists. | Skill has contract, prerequisites, failure modes, usage, guardrails, tests, and catalog update if public. |
| P1 | Define too-old nils-cli behavior for each consuming skill. | Skill reports blocked/degraded mode with upgrade command or fallback. |
| P2 | Add workflow integration after the tool skill is stable. | Workflow references the tool contract and keeps decision logic out of the tool. |
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

- Which workflow should consume `agent-scope-lock` first after manual validation
  proves useful?
- Will nils-cli expose one command per primitive, or a grouped command with
  subcommands?
- What nils-cli version floor should agent-kit require once the first primitive
  is consumed?
- Which workflow should consume `web-evidence` first now that the static HTTP
  evidence skill is public?
