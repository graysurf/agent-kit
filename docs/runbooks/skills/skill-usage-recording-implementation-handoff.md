# Skill Usage Recording Implementation Handoff

Status: Draft for discussion
Date: 2026-05-17
Source: user request plus current agent-kit skill/tooling contracts
Intended next step: review the proposed contract, then turn accepted parts into a plan or direct implementation

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
- [W1] The "Learning Beyond Gradients" article frames Heuristic Learning as code, tests, records, feedback, memory, and agent-driven updates
  rather than neural-network weight updates.

## Decisions To Review

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
    "summary": "Created draft implementation handoff",
    "artifacts": []
  },
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
- A future `skill-usage.record.v1` file for the skill invocation envelope.

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
- Prefer a nils-cli primitive for record writing and validation if this becomes machine-enforced.
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
3. Primitive validation if a nils-cli command is added:
   - unit tests in the nils-cli repo;
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

Execution state: not created yet.

Recommended execution source after review:

- If the proposal is accepted mostly as-is, create a normal implementation plan from this document.
- If the review finds major policy questions, use `review-to-improvement-doc` first to preserve review findings, then plan from the revised
  version.

Suggested pilot order:

1. Document-only pilot using `discussion-to-implementation-doc`.
2. Tool/evidence pilot using `web-qa` or `gh-fix-ci`.
3. Cross-skill promotion pilot using one repeated failure mode.

## Open Questions

1. Should every explicit skill invocation produce an artifact, or only invocations that use tools, files, external sources, validation, or
   delivery workflows?
2. Should the record live under the target project run directory, `$AGENT_HOME/out/`, or a project-defined evidence path?
3. Should skill usage records be retained by default, or cleaned after lessons are promoted?
4. Should the first implementation be a nils-cli primitive, a lightweight shell wrapper, or docs-only convention?
5. Should prompt-style conversational skills have a lighter record schema?
6. Should records be committed only when they are curated evidence, or always remain untracked runtime artifacts?

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

- an implementation plan under `docs/plans/` if this should be delivered in phases;
- a smaller direct patch if the first step is only docs/schema wording;
- a nils-cli primitive design doc if the record writer/validator should become a deterministic command.
