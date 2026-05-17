# nils-cli Workflow Primitives Finalization Implementation Handoff

Status: implementation-ready; immediate scope expanded
Date: 2026-05-17
Source: current Codex discussion plus local validation evidence
Intended next step: execute from this document, then close the acceptance gates below

## Purpose

Preserve the current `nils-cli` workflow-primitives adoption state and define the
remaining work needed before this lane can be accepted as complete in
`agent-kit`.

This handoff intentionally promotes the previously future items into immediate
implementation scope: `web-qa`, `gh-fix-ci` consumption, and active browser
automation evidence. Do not treat those items as deferred backlog unless a later
owner records a narrower decision with evidence.

## Source Register

- [U1] User request in this thread: make `web-qa`, `gh-fix-ci`, and active
  browser automation part of the immediate implementation scope; handle all
  unresolved items; write an executable handoff with final acceptance criteria.
- [F1] `docs/runbooks/nils-cli/README.md` indexes the nils-cli runbook records
  and implemented tool skills.
- [F2] `docs/runbooks/nils-cli/skill-consumable-primitives.md` records the
  primitive/adoption boundary and still contains old local-checkout and pending
  release language.
- [F3] `docs/runbooks/nils-cli/agent-kit-skill-adoption.md` lists
  `web-qa`, `gh-fix-ci`, and browser automation as later consumers.
- [F4] `skills/tools/browser/browser-session/SKILL.md` says
  `browser-session` records evidence only and does not drive the browser.
- [F5] `skills/automation/gh-fix-ci/SKILL.md` currently describes the CI
  inspection and auto-fix workflow, with a test-first evidence gate but no
  concrete consumption of the new evidence primitives.
- [A1] `agent-docs --docs-home "$AGENT_HOME" resolve --context startup
  --strict --format checklist` and `project-dev` both passed.
- [A2] `brew list --versions nils-cli` reports `nils-cli 0.8.4`, and
  `brew info nils-cli` reports the linked `sympoies/tap/nils-cli 0.8.4` keg.
- [A3] `agent-scope-lock`, `web-evidence`, `test-first-evidence`,
  `browser-session`, `canary-check`, `docs-impact`, `model-cross-check`, and
  `review-evidence` are all on `/opt/homebrew/bin` and report version `0.8.4`.
- [A4] Their help output exposes the documented subcommand surfaces:
  `agent-scope-lock create/read/validate/clear/completion`,
  `web-evidence capture/completion`,
  `test-first-evidence init/record-failing/record-waiver/record-final/verify/show/completion`,
  `browser-session init/record-step/verify/show/completion`,
  `canary-check run/verify/show/completion`,
  `docs-impact scan/completion`,
  `model-cross-check init/record-observation/verify/show/completion`, and
  `review-evidence init/record-finding/record-validation/verify/show/completion`.
- [A5] `scripts/check.sh --skills-layout` currently fails because five landed
  tool skills are missing tracked `tests/` directories:
  `skills/tools/browser/browser-session/`,
  `skills/tools/devex/canary-check/`,
  `skills/tools/devex/docs-impact/`,
  `skills/tools/devex/model-cross-check/`, and
  `skills/tools/devex/review-evidence/`.
- [A6] Both `/Users/terry/.config/agent-kit` and
  `/Users/terry/Project/sympoies/nils-cli` were clean at the start of this
  handoff, and the nils-cli checkout was on `main...origin/main` with latest
  commit `ee1f3f4 chore(release): bump cli versions to 0.8.4`.

## Confirmed Facts

- The original local-checkout-only boundary is stale on this machine. The
  workflow-primitives binaries are now available through the linked Homebrew
  `nils-cli 0.8.4` installation. [A2][A3]
- The command surfaces named by the runbooks are present for the eight current
  evidence and guardrail primitives. [A4]
- `agent-kit` is not currently accepted as complete because the skill layout gate
  fails for five tool skills that lack tracked per-skill tests. [A5]
- There is no existing `web-qa` or `browser-qa` skill directory under `skills/`.
  [F1][A5]
- `browser-session` is a record-only primitive. Active browser behavior must be
  supplied by Browser, Chrome, Playwright, or a newly implemented nils-cli
  browser driver. [F4]
- `gh-fix-ci` currently has CI inspection scripts and test-first policy wording;
  the new primitives are not yet integrated as a concrete evidence/scope
  workflow. [F5]

## Decisions

- Treat `web-qa`, `gh-fix-ci` primitive consumption, and active browser
  automation evidence as immediate scope, not future backlog. [U1]
- Keep the core boundary: `nils-cli` owns deterministic CLI behavior, schemas,
  redaction, artifacts, and validation; `agent-kit` skills own workflow
  judgment, when to invoke commands, and user-facing synthesis. [F2]
- Update stale release language to reflect Homebrew/PATH availability for
  `nils-cli 0.8.4`; keep local-checkout examples only as fallback for older or
  unreleased environments. [A2][A3]
- Prefer landing `web-qa` first as an agent-kit browser workflow skill that
  orchestrates existing Browser/Chrome/Playwright capabilities and records
  evidence with `browser-session`. Add a new nils-cli active browser driver only
  if implementation shows a deterministic CLI boundary is necessary. [F4][I1]
- Do not broaden this lane into gstack-style product review personas, unrelated
  design review, memory behavior, or continuous auto-commit policy. [F2]

## Scope

The next implementation must cover all of the following:

- Repair the current `agent-kit` acceptance gap by giving each landed workflow
  primitive tool skill tracked tests or by changing the layout policy with an
  explicit, tested exception. The default path is per-skill `tests/` directories,
  because `scripts/check.sh --skills-layout` currently requires them. [A5]
- Update nils-cli runbooks, `TOOLING_INDEX_V2.md`, and affected tool skills so
  the release state reflects `nils-cli 0.8.4` on PATH while preserving
  local-checkout fallback guidance. [A2][A3]
- Add `web-qa` as a discoverable skill with documented static and active browser
  evidence modes.
- Make active browser automation real in the `web-qa` workflow: it must open or
  inspect a browser target through Browser, Chrome, Playwright, or an explicitly
  implemented nils-cli driver, then record the actions and artifacts through
  `browser-session`.
- Update `gh-fix-ci` so its CI-fix loop consumes the evidence primitives rather
  than only describing them in prose. At minimum it must document and test how it
  records failure evidence or waivers, final validation, and scope validation.
- Update catalog/discoverability surfaces when new or changed skills become
  public entrypoints.
- Run the final validation gates listed below and keep the repo clean except for
  the intended implementation changes.

## Non-Scope

- Do not publish or manipulate secrets, cookies, auth headers, raw browser
  network logs, or unredacted CI logs.
- Do not add a second release workflow that competes with existing
  provider-scoped GitHub/GitLab workflows.
- Do not require all browser checks to go through nils-cli if Browser, Chrome,
  or Playwright remains the right active automation layer.
- Do not claim crates.io publication unless a later implementation actually
  changes nils-cli release policy. Current acceptance is based on Homebrew/PATH
  availability plus local source validation when nils-cli source changes.

## Implementation Boundaries

`agent-kit` may change:

- `docs/runbooks/nils-cli/*`
- `docs/runbooks/skills/TOOLING_INDEX_V2.md`
- `README.md` and nearby skill/catalog docs when public skill discoverability
  changes
- `skills/tools/browser/web-qa/` for the new skill
- `skills/tools/browser/browser-session/`
- `skills/tools/devex/canary-check/`
- `skills/tools/devex/docs-impact/`
- `skills/tools/devex/model-cross-check/`
- `skills/tools/devex/review-evidence/`
- `skills/automation/gh-fix-ci/`
- Tests and smoke specs required by changed entrypoints

`nils-cli` may change only if active browser automation cannot be implemented
cleanly as an agent-kit workflow over Browser/Chrome/Playwright plus
`browser-session`. If nils-cli changes are made, the implementation must also
run nils-cli checks, update generated completions as needed, and re-verify
Homebrew/PATH or local-checkout status before updating agent-kit docs.

## Requirements

### R1: Layout Gate Repair

- Add tracked tests for:
  - `skills/tools/browser/browser-session/`
  - `skills/tools/devex/canary-check/`
  - `skills/tools/devex/docs-impact/`
  - `skills/tools/devex/model-cross-check/`
  - `skills/tools/devex/review-evidence/`
- The tests must at least validate SKILL.md contract shape, documented command
  surface, artifact/schema text, release boundary, local fallback boundary, and
  guardrails.
- If the shared test at `tests/test_agent_workflow_primitives_skills.py` remains,
  it must not be the only coverage satisfying these skills.

### R2: Release-State Documentation

- Replace stale "release/Homebrew pending" language with a current
  `nils-cli 0.8.4` released PATH state.
- Keep fallback language clear: local checkout invocation is for machines where
  the required released PATH binary is absent or too old.
- Ensure no document implies `/Users/terry/.local/nils-cli/bin` is the current
  expected source for these binaries on this machine.

### R3: web-qa Skill

- Add a `web-qa` skill under the browser tooling area unless implementation
  discovers a more appropriate existing folder.
- Define two modes:
  - static evidence mode: use `web-evidence capture` when HTTP/HTTPS response
    evidence is enough.
  - active browser mode: use Browser, Chrome, Playwright, or a nils-cli driver
    when JavaScript, screenshots, console logs, authenticated browser state, or
    DOM interaction is required.
- In both modes, record the goal, steps, status, and artifact paths through
  `browser-session` when browser-session evidence is useful.
- Active browser mode must not persist raw cookies, credentials, auth headers, or
  full unredacted network logs.
- The skill must say when it is blocked, when static evidence is insufficient,
  and which browser tool should be used for logged-in or stateful sessions.

### R4: Active Browser Automation Evidence

- Provide at least one verifiable active browser workflow path that does more
  than record text:
  - opens or inspects a browser target;
  - captures an artifact such as screenshot, DOM observation, console/network
    summary, or equivalent local browser evidence;
  - records the action and artifact path with `browser-session record-step`;
  - completes with `browser-session verify`.
- The implementation may use existing Browser/Chrome/Playwright capabilities, a
  repo script, or a new nils-cli driver. The chosen boundary must be documented
  in `web-qa`.

### R5: gh-fix-ci Primitive Consumption

- Update `gh-fix-ci` so CI failure evidence can feed the test-first evidence
  contract:
  - CI failure evidence should be recorded through `test-first-evidence` when it
    is used as the failing evidence before a behavior fix.
  - A waiver path must be recorded when the CI failure cannot be reproduced or is
    docs-only, generated-only, infrastructure-only, or external-provider-only.
  - Final local validation or CI validation should be recorded before commit or
    final report.
- Add scope safety:
  - if an `agent-scope-lock` is active, validate changes before commit/push;
  - if the workflow creates a temporary lock, it must clear it on successful
    completion or document why it remains.
- Use `canary-check` for caller-owned local validation when a single command is
  the appropriate post-fix canary.
- Use `web-evidence` only for static URL evidence related to CI logs, deployment
  previews, or status pages; use `web-qa` active mode when browser behavior is
  required.

### R6: Discoverability

- Update `docs/runbooks/nils-cli/README.md` for this handoff and any new
  implemented skill.
- Update `docs/runbooks/skills/TOOLING_INDEX_V2.md` when `web-qa` or changed
  command contracts become canonical entrypoints.
- Update `README.md` only when a skill becomes part of the public catalog.

## Acceptance Criteria

This lane is accepted only when all of these are true:

- `scripts/check.sh --skills-layout` passes.
- `scripts/check.sh --docs` passes.
- `scripts/check.sh --markdown` passes.
- `scripts/check.sh --all` passes.
- The eight existing primitive binaries resolve from PATH and report the same
  released version:
  `agent-scope-lock`, `web-evidence`, `test-first-evidence`, `browser-session`,
  `canary-check`, `docs-impact`, `model-cross-check`, and `review-evidence`.
- Stale local-only or release-pending language is removed from nils-cli runbooks,
  except as explicit fallback guidance for machines without the released binary.
- The five missing tool-skill test directories exist or the layout audit has an
  intentional, tested policy exception.
- `web-qa` exists, is discoverable, has tracked tests, and documents both static
  and active browser evidence modes.
- At least one active browser evidence path is verified and recorded with
  `browser-session`.
- `gh-fix-ci` documents and tests concrete consumption of `test-first-evidence`,
  `agent-scope-lock`, `canary-check`, and `web-evidence` or `web-qa` where each
  applies.
- If nils-cli source changes were needed, nils-cli validation and release/PATH
  verification are included in the final report.

## Validation Plan

Before editing:

```bash
agent-docs --docs-home "$AGENT_HOME" resolve --context startup --strict --format checklist
agent-docs --docs-home "$AGENT_HOME" resolve --context project-dev --strict --format checklist
git status --short --branch
```

During implementation, use focused checks:

```bash
scripts/check.sh --skills-layout
scripts/check.sh --tests -- -k 'agent_workflow_primitives_skills or browser_session or canary_check or docs_impact or model_cross_check or review_evidence or web_qa or gh_fix_ci'
scripts/check.sh --docs
scripts/check.sh --markdown
```

Before reporting complete:

```bash
scripts/check.sh --all
for cmd in agent-scope-lock web-evidence test-first-evidence browser-session canary-check docs-impact model-cross-check review-evidence; do
  command -v "$cmd"
  "$cmd" --version
done
brew list --versions nils-cli
```

If nils-cli source changes are made, run the nils-cli repository's required test
and release-readiness gates from `/Users/terry/Project/sympoies/nils-cli`, then
verify the resulting PATH or local-checkout boundary before changing agent-kit
release claims.

## Risks And Guardrails

- Do not let `web-qa` become a vague product-review skill. It must be an evidence
  workflow with explicit artifact and redaction behavior.
- Do not pretend `browser-session` drives a browser. It records evidence; another
  layer must perform active operations.
- Do not make `gh-fix-ci` bypass project-defined CI, release, or test-first
  gates. New primitives should improve evidence and safety, not widen unattended
  edits.
- Do not mix PATH binaries and local cargo invocations in the same evidence
  claim without explaining which source was used.
- Do not commit raw run artifacts, browser cookies, auth headers, or unredacted
  logs.

## Execution

Execution source of truth: this document.

Active execution-state path:
`docs/runbooks/nils-cli/workflow-primitives-finalization-execution-state.md`.

That file tracks which requirements above are complete, which validations
passed, and any intentional deviations. If the work is split into PRs or sprint
lanes, create a plan after reading this document and link the plan back here as
read-first context.

## Open Questions

- Can active browser automation be fully implemented as an agent-kit `web-qa`
  workflow over Browser/Chrome/Playwright plus `browser-session`, or is a new
  nils-cli browser driver needed? Default: implement the agent-kit workflow first
  and only add nils-cli source work if the evidence contract cannot be made
  deterministic enough.
- Should `gh-fix-ci` add script flags such as `--evidence-out` or keep primitive
  calls in the surrounding workflow instructions? Default: add script support
  only where tests can prove deterministic behavior; otherwise keep direct
  command invocation explicit in the skill workflow.

## Read-First References

- `docs/runbooks/nils-cli/README.md`
- `docs/runbooks/nils-cli/skill-consumable-primitives.md`
- `docs/runbooks/nils-cli/agent-kit-skill-adoption.md`
- `docs/runbooks/nils-cli/test-first-evidence-contract.md`
- `docs/runbooks/skills/TOOLING_INDEX_V2.md`
- `skills/tools/browser/browser-session/SKILL.md`
- `skills/tools/browser/web-evidence/SKILL.md`
- `skills/automation/gh-fix-ci/SKILL.md`

## Recommended Next Artifact

Use `execute-from-implementation-doc` against this file when the next session is
ready to implement. Use `create-plan` only if the executor needs PR splitting,
task ownership lanes, or multi-repo sequencing before code changes.
