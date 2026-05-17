# nils-cli Skill-Consumable Primitives Improvement Record

Status: active; first primitive set implemented in `nils-cli`
Date: 2026-05-17
Scope: `nils-cli` capabilities consumed by agent-kit skills

## Purpose

Prepare the implementation boundary for moving high-value, repeatable skill
behavior into stable `nils-cli` commands.

This is not an implementation plan. It records the current judgment, command
contracts that have landed, remaining candidate tool contracts, acceptance
gates, and guardrails that later implementation sessions should treat as
read-first context.

Implementation update (2026-05-17):

- Implemented primitive: `agent-scope-lock`.
- nils-cli package/binary: `nils-agent-scope-lock` / `agent-scope-lock`.
- Implemented command surface: `create`, `read`, `validate`, `clear`,
  `completion`.
- Implemented primitive: `web-evidence`.
- nils-cli package/binary: `nils-web-evidence` / `web-evidence`.
- Implemented command surface: `capture`, `completion`.
- Version/release boundary: workspace version `0.8.3`; released skill contracts
  should require the nils-cli release artifact that includes the needed package.
- Local verification snapshot (2026-05-17): this machine has PATH-installed
  `agent-scope-lock`, `web-evidence`, `agent-docs`, `plan-issue`,
  `test-first-evidence`, `browser-session`, `canary-check`, `docs-impact`,
  `model-cross-check`, and `review-evidence` reporting version `0.8.3`.
  The six newest binaries are installed from the local nils-cli checkout under
  `/Users/terry/.local/nils-cli/bin`. Future sessions should re-check live PATH
  state before making release or machine-local claims.
- Agent-kit adoption boundary: `skills/tools/devex/agent-scope-lock/` and
  `skills/tools/browser/web-evidence/` are the first consuming skills. They may
  use commands from a validated local `nils-cli` checkout before the release is
  installed on PATH.
- Agent-kit workflow update: `web-evidence` is now consumed by release and
  issue-follow-up workflows for static HTTP/HTTPS evidence, and
  `agent-scope-lock` is now wired into Codex hooks as an active-lock guard.
- Test-first update: behavior-editing workflows and PR/MR templates now surface
  failing-test evidence or explicit waivers. `nils-cli` now has an implemented
  `test-first-evidence` crate/command with publish dry-run evidence, and
  agent-kit has a tool skill contract for PATH or validated local-checkout usage.
- Agent workflow primitives update: `nils-cli` now has the
  `nils-agent-workflow-primitives` package with `browser-session`,
  `canary-check`, `docs-impact`, `model-cross-check`, and `review-evidence`
  binaries. The first slice is deterministic local evidence and repo scanning:
  browser/model provider execution remains owned by browser/provider workflows.
  Agent-kit tool skill contracts have landed for all five commands.
- Release/PATH boundary: these new binaries now exist on this machine's PATH via
  local install from the current nils-cli checkout. Distributable release
  artifacts and Homebrew/crates.io publication are still pending; on other
  machines, use the documented local-checkout `cargo run --locked
  --manifest-path ... -p nils-agent-workflow-primitives --bin <binary> -- ...`
  form until a release artifact includes `nils-agent-workflow-primitives`.

Companion record:
`docs/runbooks/nils-cli/agent-kit-skill-adoption.md` describes how agent-kit
skills should adopt these primitives after nils-cli command contracts stabilize.
`docs/runbooks/nils-cli/test-first-evidence-contract.md` records the landed
workflow-level test-first evidence contract and nils-cli primitive, with local
PATH install complete and distributable release adoption pending.

## Context

Source facts:

- agent-kit positions `nils-cli` as the provider for shared helper binaries used
  by skills and checks, including `agent-docs`, `plan-issue`, `plan-tooling`,
  `api-*`, `semantic-commit`, `agent-out`, and media tooling.
- The public skill catalog already relies on CLI-backed workflows for API tests,
  semantic commits, screenshots, screen recording, image processing, plan
  tooling, and artifact directories.
- Existing browser skills are wrappers around external `npx` packages or native
  Browser/Chrome capabilities; they do not define an agent-kit-owned browser
  evidence contract.
- The user-approved design direction is to put important, well-understood,
  deterministic behavior in `nils-cli`, while leaving workflow judgment in
  skills.

Assumptions:

- `nils-cli` changes will happen in the `nils-cli` repository, not directly in
  this agent-kit repository.
- agent-kit should document the desired skill-facing contracts before adding or
  changing skills that depend on new commands.
- Browser and web QA functionality should start with local, auditable evidence
  capture before considering remote pairing, side panels, or long-lived
  cross-agent coordination.

Inference:

- The right abstraction boundary is command output and artifacts, not prompt
  prose. Skills should decide when to invoke a capability and how to interpret
  results; `nils-cli` should own deterministic execution, stable schemas, path
  discipline, and failure classification.

## Current Judgment

Start with `nils-cli` primitives that multiple skills can share and that have
clear acceptance gates:

- Produce deterministic stdout or JSON.
- Write artifacts only to canonical `agent-out` locations unless an explicit
  output path is provided.
- Classify failures in machine-readable terms.
- Avoid raw secrets, credentials, cookies, and unredacted logs in persisted
  artifacts.
- Prefer dry-run and inspect modes before write or network-heavy behavior.
- Provide focused unit tests plus one smoke path that can run in agent-kit CI or
  a nils-cli release gate.

Do not start by importing broad product-review, design-taste, proactive
suggestion, continuous auto-commit, or long-term memory behavior into `nils-cli`.
Those remain skill or policy experiments until their contracts are stable.

## Candidate CLI Primitives

| Priority | Candidate | Skill consumers | Why it belongs in `nils-cli` | Minimum acceptance |
| --- | --- | --- | --- | --- |
| P1 | `browser-session` | Landed tool skill; later: future `web-qa`, `release-workflow`, `screenshot`, `agent-browser` replacement | Browser evidence needs a stable local record instead of repeated prompt prose. | Implemented first slice as `init/record-step/verify/show/completion` with `browser-session.json`; it records target, goal, step status, and artifacts. It does not open or drive a browser. |
| P1 | `web-evidence` | Landed: `release-workflow`, `issue-follow-up`; later: future `web-qa`, `gh-fix-ci` | Multiple workflows need the same URL evidence bundle shape. | Implemented first slice in `nils-cli` as static HTTP evidence: `summary.json`, `headers.redacted.json`, and `body-preview.redacted.txt`; browser screenshots, console logs, and browser network summaries remain future browser-session scope. |
| P1 | `agent-scope-lock` | Landed: Codex hook guard; later: `find-and-fix-bugs`, `gh-fix-ci`, `plan-issue-delivery`, future debug workflows | Directory/file edit boundaries should be mechanically checkable, not only prompt instructions. | Implemented in `nils-cli` as `agent-scope-lock create/read/validate/clear`; PATH usage requires the nils-cli release containing workspace version `0.8.3` or newer. |
| P2 | `docs-impact` | Landed tool skill; later: `release-workflow`, document-release-style future skill, docs maintenance | Diff-to-docs drift should be detected before asking a skill to rewrite docs. | Implemented first slice as `scan/completion`; it classifies Git changed files into docs and non-docs and emits `suggested_review`. It does not rewrite docs. |
| P2 | `review-evidence` | Landed tool skill; later: `review-to-improvement-doc`, PR review workflows, `issue-pr-review` | Findings from different reviewers or tools need a normalized, mergeable record. | Implemented first slice as `init/record-finding/record-validation/verify/show/completion` with `review-evidence.json`; `verify` requires passing validation and no open high/medium findings. |
| P2 | `test-first-evidence` | Landed: `find-and-fix-bugs`, `fix-bug-pr`, `gh-fix-ci`, `issue-subagent-pr`, `execute-plan-parallel`, PR/MR creation workflows; tool skill landed under DevEx | Failing-test evidence and waiver records should be normalized instead of recreated in every skill. | Implemented in `nils-cli` as `test-first-evidence init/record-failing/record-waiver/record-final/verify/show/completion`; local PATH install from this checkout is verified on this machine, and release artifact adoption remains pending. |
| P2 | `canary-check` | Landed tool skill; later: `release-workflow`, future `land-and-deploy`, future `web-qa` | Post-change checks need repeatable pass/fail evidence. | Implemented first slice as `run/verify/show/completion`; it runs one local command, redacts stdout/stderr previews, and writes `canary-check.json`. Deploy-target orchestration remains future workflow scope. |
| P3 | `model-cross-check` | Landed tool skill; later: review workflows, research workflows | Cross-model review is valuable but provider/auth/state handling must be narrow and explicit. | Implemented first slice as `init/record-observation/verify/show/completion` with `model-cross-check.json`; provider calls, cost tracking, and model routing remain outside this CLI. |

## Ownership Boundary

`nils-cli` should own:

- CLI parsing, validation, and error codes.
- Machine-readable output schemas.
- Canonical artifact layout and cleanup behavior.
- Redaction and secret-safety defaults.
- Low-level browser/process lifecycle where applicable.
- Unit and smoke tests for command contracts.

agent-kit skills should own:

- When a command should run.
- How much evidence is enough for the user request.
- Whether a finding should become a fix, issue, improvement doc, PR, or handoff.
- User-facing synthesis and tradeoff judgment.
- Provider-specific delivery policy, such as GitHub PR versus GitLab MR flow.

## Backlog

| Priority | Work item | Acceptance |
| --- | --- | --- |
| P1 | Define a stable JSON schema pattern for new `nils-cli` commands. | At least `status`, `version`, `command`, `cwd`, `artifacts`, `findings`, and `errors` fields are specified or deliberately excluded. |
| P1 | Prototype the first P1 primitives in nils-cli first, not as skill-local scripts. | `agent-scope-lock`, `web-evidence`, `test-first-evidence`, and the first `nils-agent-workflow-primitives` binary set exist as implemented primitives and can be consumed without shell parsing beyond command invocation. |
| P1 | Add agent-kit docs for chosen commands once the nils-cli contract exists. | `docs/runbooks/skills/TOOLING_INDEX_V2.md` and tool skills list implemented commands with version/release boundaries. |
| P2 | Evaluate replacing the legacy `agent-browser` wrapper after an agent-kit-owned browser contract exists. | Existing `agent-browser` references have a migration note or remain explicitly legacy. |
| P2 | Add scope lock hook integration only after the CLI validator is stable. | Done: Codex hook guard validates active locks and reports concise violations with the validation command. |

## Validation Gate

Before reporting any nils-cli primitive complete:

- nils-cli command help is stable and includes examples.
- JSON output has fixture tests.
- Failure modes have at least one test each for invalid input and missing
  dependency.
- Agent-kit skill contract references the command without duplicating its full
  implementation details and has focused skill-governance coverage.
- agent-kit docs checks pass after adding the skill-facing documentation:
  `scripts/check.sh --docs` and `scripts/check.sh --markdown`.

Before expanding browser or web-evidence primitives:

- Artifacts must be written under a single run directory.
- Console and network logs must be summarized or redacted by default.
- Auth/cookie handling must be explicit opt-in.
- Cleanup must be idempotent.
- Headed/manual handoff behavior must be optional and separate from the base
  evidence contract.

## Do Not Do

- Do not add broad gstack-style product, CEO, or design review behavior to
  `nils-cli`; keep that in skills or prompts.
- Do not make continuous auto-commit a default CLI behavior.
- Do not let a browser primitive persist raw cookies, credentials, or full
  unredacted network logs.
- Do not list candidate commands in the canonical tooling index until they
  exist and have tests.
- Do not make a skill depend on a new command before documenting the nils-cli
  version floor and fallback behavior.

## Open Questions

- Which workflow should consume the new `docs-impact`, `review-evidence`, and
  `canary-check` tool contracts first after real-use feedback?
- Should future browser work keep `browser-session` as a record-only evidence
  primitive, or add a second active browser automation slice that can open pages
  and collect screenshots/console/network summaries?
- Which workflow should adopt `agent-scope-lock` next after the Codex hook guard
  has enough real-use history: `gh-fix-ci`, `find-and-fix-bugs`, or
  `plan-issue-delivery`?
