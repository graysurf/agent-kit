# nils-cli Runbooks

This directory holds durable notes for `nils-cli` capabilities that agent-kit
skills should consume as stable CLI contracts.

- [Skill-Consumable Primitives](./skill-consumable-primitives.md): improvement
  record for candidate `nils-cli` primitives that should move repeated,
  deterministic skill behavior out of prompt logic and shell snippets.
- [Agent-kit Skill Adoption Architecture](./agent-kit-skill-adoption.md):
  companion record for how agent-kit skills should land around future
  `nils-cli` primitives once their actual command contracts stabilize.
- Implemented tool skills: `skills/tools/devex/agent-scope-lock/` and
  `skills/tools/browser/web-evidence/`.
- [Test-First Evidence Contract](./test-first-evidence-contract.md):
  improvement record for requiring failing-test evidence or an explicit waiver
  before production behavior changes.
