## Decision

- Decision: `<merge|request-followup|close-pr>`
- Task lane: `<Owner / Branch / Worktree / Execution Mode / PR>`

## Review Scope

- Scope baseline: `<plan task snippet/link + dispatch record id/path>`
- PR reviewed: `#<number>`
- Scope exclusions checked: `<yes/no + evidence>`

## Hard Gates

- PR linkage + lane facts: `<pass|fail|blocked>` (evidence: `<issue row / lane facts>`)
- PR body hygiene: `<pass|fail|blocked>` (evidence: `<validator result / headings check>`)
- Validation evidence present: `<pass|fail|blocked>` (evidence: `<test command/output reference>`)
- CI/check status: `<pass|fail|blocked>` (evidence: `<gh pr checks summary/link>`)

## Task Fidelity

- Scope verdict: `<pass|fail|blocked>` (evidence: `<diff path(s) + task requirement mapping>`)

## Correctness

- Correctness verdict: `<pass|fail|blocked>` (evidence: `<behavior/risk analysis + test evidence>`)

## Integration Readiness

- Integration verdict: `<pass|fail|blocked>` (evidence: `<dependency/gate impact evidence>`)

## Evidence Links

- Diff refs: `<path:line or commit/PR diff anchors>`
- Validation refs: `<commands + pass/fail output>`
- CI refs: `<check names + URLs>`
- Residual risk: `<explicit remaining risk or none>`
