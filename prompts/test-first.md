---
description: Require failing-test evidence or an explicit waiver before production code changes.
argument-hint: implementation task
---

Use **test-first implementation mode** for this task.

USER TASK $ARGUMENTS

CONTEXT (optional but recommended)

- Target behavior / bug: <...>
- Done criteria: <...>
- Relevant files or modules: <...>
- Test command, if known: <...>
- Constraints / risks: <...>

RULES (must follow)

1. Classify the change before editing production code
   - Decide whether the request changes testable production behavior.
   - Treat bug fixes, parser logic, state machines, API contracts, workflow logic, user-visible behavior, and new features as testable by
     default.
   - Docs-only, generated-only, formatting-only, visual-only, exploratory spikes, emergency hotfixes, or repos with no usable test harness
     may use a waiver.

2. Failing test first
   - If this is a testable production behavior change, add or identify a focused regression, unit, integration, or acceptance test before
     editing production code.
   - Run the test and capture failing evidence before production edits:
     - command
     - exit code
     - failing test file or test name
     - concise failure summary
   - Do not weaken, skip, or overfit the test to the planned implementation.

3. Waiver when test-first does not apply
   - If no failing test is practical, state the waiver before editing production code.
   - Include:
     - waiver reason
     - why a failing test is not practical now
     - substitute validation you will run

4. Implement after evidence
   - Only edit production code after recording failing evidence or a waiver.
   - Keep the production change scoped to making the failing test pass.
   - Add broader tests only when the blast radius or shared contract justifies it.

5. Final validation
   - Re-run the failing test and the smallest meaningful related validation.
   - Report final validation with command, result, and any skipped checks.

FINAL RESPONSE MUST INCLUDE

- Change classification
- Failing-test evidence, or waiver reason
- Production files changed
- Final validation commands and results
- Remaining risk, if any
