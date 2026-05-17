# Skill Usage Recording Implementation Handoff

Status: Implemented; nils-cli primitive released through Homebrew
Date: 2026-05-17
Source: user request plus current agent-kit skill/tooling contracts
Intended next step: use accumulated records to promote the first repeated
failure into durable skill docs, tests, scripts, primitives, or runbook guidance

## Purpose

Define a repo-wide convention for recording skill usage outcomes, especially failures, repairs, and follow-up handling, so future agents can
learn from repeated workflow experience without relying on hidden model memory or ad hoc session notes.

The goal is to make skill execution behave like an explicit heuristic learning loop:

1. A skill is selected and run.
2. The agent records the context, outcome, validation, and any failure.
3. If the skill or script fails, the agent records how it diagnosed, handled, or fixed the issue.
4. Repeated or important failures are promoted into durable skill docs, tests, scripts, or primitives.
5. Periodic maintenance compresses noisy history into smaller, clearer contracts.

## Confirmed Facts

- [U1] The desired behavior is automatic record keeping whenever skills are used.
- [U1] Error handling should include how the agent corrected or handled the failure.
- [U1] The first deliverable should be a written specification for discussion and review, not implementation.
- [F1] Tracked skills already have a standard anatomy: `SKILL.md`, optional `scripts/`, optional `references/`, optional `assets/`, and
  required `tests/`.
- [F2] Existing workflow primitives already record typed evidence, including `test-first-evidence`, `browser-session`, `canary-check`,
  `docs-impact`, `model-cross-check`, and `review-evidence`.
- [F3] Existing repo policy keeps deterministic evidence and guardrail primitives in nils-cli, while skills keep workflow framing,
  judgment, and repo-local policy.
- [F4] nils-cli implements `skill-usage` under `nils-agent-workflow-primitives`, with agent-kit consuming it through
  `skills/tools/devex/skill-usage/SKILL.md`.
- [F5] nils-cli v0.8.5 was released through `sympoies/tap`; local Homebrew install now provides `skill-usage 0.8.5` on PATH.
- [W1] The "Learning Beyond Gradients" article frames Heuristic Learning as code, tests, records, feedback, memory, and agent-driven updates
  rather than neural-network weight updates.

## Decisions To Review

The docs-first subset below is implemented in
`docs/runbooks/skills/SKILL_USAGE_RECORDING_V1.md`. Writer/validator behavior is
now implemented as the nils-cli `skill-usage` primitive and released through
Homebrew in nils-cli v0.8.5 while workflow policy remains in agent-kit.

### 1. Record every skill invocation at the workflow boundary

Every explicit skill use should produce a compact invocation record unless the skill is purely conversational and the user explicitly asks not
to retain artifacts.

Minimum fields:

```json
{
  "schema": "skill-usage.record.v1",
  "skill": "skills/workflows/conversation/discussion-to-implementation-doc",
  "started_at": "2026-05-17T00:00:00+08:00",
  "cwd": "/path/to/repo",
  "trigger": "user_explicit",
  "intent": "draft implementation handoff",
  "inputs": {
    "user_request_summary": "Write a draft spec for automatic skill usage records",
    "referenced_files": [],
    "external_sources": []
  },
  "outcome": {
    "status": "pass",
    "summary": "Created draft implementation handoff"
  },
  "artifacts": [],
  "validation": [],
  "follow_up": []
}
```

### 2. Use typed child records instead of one large log file

The top-level skill usage record should link to specialized evidence records rather than duplicate them.

Examples:

- `test-first-evidence.json` for before/after test evidence.
- `browser-session.json` for active browser QA.
- `canary-check.json` for one local canary command.
- `review-evidence.json` for review findings or validation records.
- `skill-usage.record.v1` for the skill invocation envelope.

This keeps the record readable while preserving machine-verifiable evidence where it already exists.

### 3. Standardize failure handling records

When a skill, script, command, or dependency fails, the agent should record a failure item with enough detail for the next agent to avoid
repeating blind diagnosis.

Minimum fields:

```json
{
  "phase": "preflight|execution|validation|cleanup|delivery",
  "command": "scripts/check.sh --docs",
  "exit_code": 1,
  "symptom": "docs freshness check failed",
  "classification": "skill_contract|script_bug|missing_dependency|external_service|project_state|user_scope|unknown",
  "diagnosis": "The new doc was not linked from the expected docs index.",
  "handling": "Updated the nearest docs index and reran docs check.",
  "result": "fixed|worked_around|blocked|accepted_risk",
  "artifacts": []
}
```

The failure record should distinguish:

- What failed.
- Why the agent thinks it failed.
- Whether the issue was fixed, worked around, blocked, or accepted as risk.
- Which command or artifact verifies the final state.

### 4. Promote repeated failures into durable knowledge

Usage records should not accumulate forever as isolated logs. A repeated or high-impact failure should be promoted through a small ladder:

| Signal | Durable action |
| --- | --- |
| First isolated failure | Record in `skill-usage.record.v1` and cite final validation. |
| Repeated failure in the same skill | Add or update `Failure modes` in `SKILL.md` or `references/`. |
| Failure is reproducible | Add a focused test or script smoke fixture. |
| Failure is cross-skill | Add a shared primitive, guardrail, or runbook section. |
| Failure comes from unclear user/workflow policy | Update the relevant workflow skill or home-scope policy after review. |

### 5. Add compression as an explicit maintenance operation

Automatic records are useful only if they can be compressed into durable rules.

Recommended compression loop:

1. Review accumulated usage records for one skill.
2. Group failures by classification and root cause.
3. Delete or archive noisy records only after the durable lesson is represented elsewhere.
4. Convert repeated lessons into one of:
   - a clearer `SKILL.md` contract;
   - a `Failure modes` entry;
   - a test;
   - a script guardrail;
   - a nils-cli primitive;
   - a short runbook reference.
5. Keep the skill surface smaller after compression than before.

## Scope

This proposal covers:

- Explicit skill invocations.
- Scriptless workflow skills when the agent follows a named skill.
- Skill-local scripts and referenced nils-cli primitives.
- Failure diagnosis and recovery records.
- Promotion of repeated failures into docs, tests, scripts, or primitives.
- Retention boundaries for generated evidence.

## Non-Scope

This proposal does not cover:

- Hidden chain-of-thought or private model reasoning.
- Secret material, raw credentials, API keys, auth cookies, or unredacted logs.
- Full telemetry collection for every shell command outside skill workflows.
- Automatic self-modification of skills without review, tests, and version control.
- Replacing existing evidence primitives such as `test-first-evidence` or `browser-session`.

## Implementation Boundaries

- Keep the top-level skill usage record small and stable.
- Use the nils-cli `skill-usage` primitive for record writing and validation when available.
- Do not hand-edit generated JSON evidence in normal workflows.
- Do not require every conversational prompt-style skill to write repo artifacts unless the user requested durable output or the skill touches
  files, tools, external sources, or validation.
- Redact secret-like values in all recorded command text, logs, URLs, headers, and environment excerpts.
- Let project-local `AGENTS.md` or closer docs override retention and artifact paths.

## Requirements

1. A skill usage record must be created for explicit skill execution when the workflow performs file edits, tool/API calls, validation, or
   external lookup.
2. The record must identify the skill, trigger, working directory, intent, start/end status, artifacts, and validation.
3. Failures must include phase, symptom, classification, diagnosis, handling, result, and verifying evidence when available.
4. Existing typed evidence records must be linked rather than duplicated.
5. Records must be redacted and safe to retain.
6. The workflow must define how a failure graduates from one-off evidence into durable skill/docs/tests/tooling changes.
7. The workflow must define a compression step so local patches do not accumulate into unmaintainable skill policy.

## Acceptance Criteria

- A draft schema exists for `skill-usage.record.v1`.
- A skill workflow can record a successful invocation and a failed invocation.
- Records can link to existing evidence artifacts.
- A validator can reject records missing status, failure classification, or final validation when required.
- At least one pilot skill documents how it uses the record.
- At least one repeated failure is promoted into a durable `Failure modes` entry or test during a pilot.
- The docs explain when no record is required.

## Validation Plan

During implementation, validate in layers:

1. Documentation validation:
   - `scripts/check.sh --docs`
   - `scripts/check.sh --markdown`
2. Contract validation if SKILL.md files change:
   - `skills/tools/skill-management/skill-governance/scripts/validate_skill_contracts.sh`
   - `skills/tools/skill-management/skill-governance/scripts/audit-skill-layout.sh`
3. Primitive validation if a nils-cli command changes:
   - unit and integration tests in the nils-cli repo;
   - local PATH or local checkout boundary checks;
   - record redaction tests.
4. Pilot validation:
   - run one selected skill through a success path;
   - run or simulate one failure path;
   - verify the generated record and linked evidence.

## Risks And Guardrails

| Risk | Guardrail |
| --- | --- |
| Records become noisy and ignored. | Keep invocation records compact and require periodic compression. |
| Sensitive data leaks into retained artifacts. | Redact by default and reject raw credentials, cookies, tokens, private keys, and unredacted logs. |
| Agents overfit to old failures. | Promote repeated lessons into tests and contracts, not only memory-like notes. |
| Skill usage becomes too heavy for small conversations. | Require records only for explicit skills with durable work, tools, validation, external lookup, or file edits. |
| Generated records become another hand-maintained format. | Prefer a nils-cli primitive with schema validation if machine enforcement is adopted. |
| The proposal blurs skill vs primitive boundaries. | Keep record storage/validation in primitives; keep judgment and promotion rules in skills/runbooks. |

## Execution

Execution state:
`docs/runbooks/skills/skill-usage-recording-implementation-handoff-execution-state.md`

Implemented docs-first artifacts:

- Canonical convention:
  `docs/runbooks/skills/SKILL_USAGE_RECORDING_V1.md`
- Draft schema:
  `docs/runbooks/skills/skill-usage-record-v1.schema.json`
- Repo-local validator:
  `scripts/skills/validate_skill_usage_record.py`
- Pilot skill wording:
  `skills/workflows/conversation/discussion-to-implementation-doc/SKILL.md`
- nils-cli primitive:
  `skill-usage` from nils-cli v0.8.5 or newer
- Installed-binary pilot record:
  `/Users/terry/.config/agent-kit/out/projects/graysurf__agent-kit/20260517-224427-skill-usage-homebrew-pilot/skill-usage/skill-usage.record.json`

Implemented follow-up decisions:

- Promote `skill-usage.record.v1` writer/validator behavior into the nils-cli
  `skill-usage` primitive.
- Retention precedence is project-defined evidence path first,
  `agent-out project --topic skill-usage --mkdir` second, and `$AGENT_HOME/out/`
  only as home-scope fallback.
- Generated runtime records remain untracked by default. Commit only curated
  review, incident, audit, fixture, or compressed durable records.
- Prompt-style conversational skills do not get a separate schema yet. Use no
  record for pure conversation; use full `skill-usage.record.v1` only when there
  is durable work, tooling, external lookup, or validation.

Recommended execution source after review:

- If the proposal is accepted mostly as-is, create a normal implementation plan from this document.
- If the review finds major policy questions, use `review-to-improvement-doc` first to preserve review findings, then plan from the revised
  version.

Pilot status:

1. Document-only pilot wiring is documented in `discussion-to-implementation-doc`.
2. Installed-binary success pilot is retained under the project-scoped
   `agent-out` run directory listed above.
3. Cross-skill repeated-failure promotion remains pending until enough real
   failure records accumulate.

## Answered Decisions

1. Records are required for explicit skills that use tools, files, external
   sources, validation, delivery workflows, or durable artifacts. Pure
   conversational prompt-style skills do not require records.
2. Records prefer a project-defined evidence path, then a project-scoped
   `agent-out` run directory, with `$AGENT_HOME/out/` only as fallback.
3. Runtime records stay untracked by default and should be cleaned or compressed
   after their lesson is represented in durable docs, tests, scripts, or
   primitives.
4. The first implementation is docs-first in agent-kit, followed by a nils-cli
   primitive for deterministic writer/validator behavior.
5. Prompt-style conversational skills should not get a separate lighter schema
   yet. Use no record for pure conversation, or full `skill-usage.record.v1`
   with `validation_required=false` and `validation_waiver` for rare retained
   lightweight cases.
6. Records should be committed only when curated as review, incident, audit,
   fixture, or compressed durable evidence.

## Remaining Questions

1. Which accumulated repeated failure should be the first compression/promotion
   pilot.

## Read-First References

- `docs/runbooks/skills/SKILLS_ANATOMY_V2.md`
- `docs/runbooks/skills/SKILL_REVIEW_CHECKLIST.md`
- `docs/runbooks/skills/TOOLING_INDEX_V2.md`
- `skills/tools/devex/test-first-evidence/SKILL.md`
- `skills/tools/browser/browser-session/SKILL.md`
- `skills/tools/devex/review-evidence/SKILL.md`
- `skills/automation/gh-fix-ci/SKILL.md`
- [Learning Beyond Gradients](https://trinkle23897.github.io/learning-beyond-gradients/)

## Recommended Next Artifact

After review, create one of:

- a short promotion record once a real repeated failure has generated enough
  success/failure evidence to justify durable skill, test, script, primitive, or
  runbook changes.
