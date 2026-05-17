# Skill-Dev Workflow

## Scope

- Canonical required workflow for `skill-dev` context.
- Applies to skill creation, updates, governance checks, and skill script validation.
- Includes the root Heuristic System framework as read-first context for skill lifecycle work.

## Entry commands

1. `agent-docs --docs-home "$AGENT_HOME" resolve --context startup --strict --format checklist`
2. `agent-docs --docs-home "$AGENT_HOME" resolve --context skill-dev --strict --format checklist`
3. `agent-docs --docs-home "$AGENT_HOME" resolve --context task-tools --format checklist` (optional, when external tool/document lookup is needed)
4. `agent-docs --docs-home "$AGENT_HOME" baseline --check --target all --strict --format text` (only when strict resolve fails)

## Deterministic flow

1. Resolve `startup` in strict mode before any skill preflight.
2. Resolve `skill-dev` in strict mode before touching `skills/**`.
3. Read `HEURISTIC_SYSTEM.md` before changing skill contracts, scripts, references, tests, or workflow primitives.
4. Treat `HEURISTIC_SYSTEM.md` as recommended read-first context when explicitly using a skill whose behavior depends on retained evidence,
   failure handling, or promotion of lessons into durable repo knowledge.
5. Follow skill contract format and repository skill governance rules.
6. Validate skill contract/layout/tests before reporting completion.
7. Keep changes scoped to intended skill paths and referenced assets/scripts.

## Failure handling

- `startup` strict resolve fails:
  - Block skill file edits.
  - Run strict baseline check and report missing docs.
  - Resume only after required docs are present.
- `skill-dev` strict resolve fails:
  - Block skill file edits.
  - Run strict baseline check and report missing docs.
  - Resume only after required docs are present.
- Skill governance/test validation fails:
  - Report failing command and key output.
  - Do not claim skill task completion.

## Validation checklist

- [ ] `agent-docs --docs-home "$AGENT_HOME" resolve --context startup --strict --format checklist` exits 0 before skill edits.
- [ ] `agent-docs --docs-home "$AGENT_HOME" resolve --context skill-dev --strict --format checklist` exits 0 before skill edits.
- [ ] `HEURISTIC_SYSTEM.md` has been read when the change affects skill lifecycle or skill evidence/failure-handling behavior.
- [ ] Skill contract validation and required checks are executed.
- [ ] Validation failures are surfaced with command-level details.
