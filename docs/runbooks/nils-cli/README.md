# nils-cli Runbooks

This directory holds durable notes for current and candidate `nils-cli`
capabilities that agent-kit skills should consume as stable CLI contracts.

- [Skill-Consumable Primitives](./skill-consumable-primitives.md): improvement
  record for landed and candidate `nils-cli` primitives that move repeated,
  deterministic skill behavior out of prompt logic and shell snippets.
- [Agent-kit Skill Adoption Architecture](./agent-kit-skill-adoption.md):
  companion record for how agent-kit skills should land around implemented and
  future `nils-cli` primitives once their actual command contracts stabilize.
- Implemented tool skills: `skills/tools/devex/agent-scope-lock/`,
  `skills/tools/browser/web-evidence/`,
  `skills/tools/devex/test-first-evidence/`,
  `skills/tools/browser/browser-session/`,
  `skills/tools/devex/canary-check/`,
  `skills/tools/devex/docs-impact/`,
  `skills/tools/devex/model-cross-check/`, and
  `skills/tools/devex/review-evidence/`.
- [Test-First Evidence Contract](./test-first-evidence-contract.md):
  improvement record for requiring failing-test evidence or an explicit waiver
  before production behavior changes.
