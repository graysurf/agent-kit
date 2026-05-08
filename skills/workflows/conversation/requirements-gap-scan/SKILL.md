---
name: requirements-gap-scan
description:
  Use when the user explicitly asks for a requirements gap scan, missing-context checklist, or clarification pass before
  implementation.
  Also use its question format when a task is genuinely blocked by missing must-have details.
---

# Requirements Gap Scan

## Contract

Prereqs:

- User explicitly invokes this skill or asks for a pre-implementation gap scan, missing-context checklist, or clarification pass; or
- A task is blocked because objective, scope, done criteria, constraints, environment, or safety/reversibility are materially unclear.
- User is available to answer questions, choose suggested defaults, or explicitly approve stated assumptions.

Inputs:

- User request + any provided context (codebase, environment, constraints, examples).
- Optional mode:
  - `gap-scan`: brainstorm what is underspecified, including nice-to-decide items.
  - `blocking`: ask only must-have questions required before action.
- Optional user preference for defaults vs custom answers (for example, "defaults").

Outputs:

- `gap-scan`: a compact requirements-gap checklist with `Must Decide`, `Nice To Decide`, `Suggested Defaults`, and `Risks`.
- `blocking`: 1-5 numbered "Need to know" questions with short options and an explicit default.
- If the user asks to proceed without answers: a short numbered assumptions list to confirm before starting work.

Exit codes:

- N/A (conversation workflow; no repo scripts)

Failure modes:

- User cannot provide required answers and will not approve assumptions when the task is blocked.
- Constraints conflict or request stays ambiguous after Q/A.
- The skill is used as a generic delay before ordinary implementation work instead of following `AGENTS.md` safe-assumption defaults.

## Goal

Help the user make vague work concrete. This explicit-first skill replaces the old `ask-questions-if-underspecified` name with a
requirements-gap scan. Use it when the user wants Codex to find missing requirements, or when missing details would make action risky or
wrong.

Do not use this skill as the default behavior for ordinary implementation requests. If assumptions are low-risk, follow `AGENTS.md`:
state the assumptions briefly and proceed.

## Workflow

1. Choose the mode
   - Use `gap-scan` when the user asks to brainstorm missing requirements, clarify scope, or identify what has not been decided yet.
   - Use `blocking` when action would be risky, wrong, irreversible, or materially incomplete without user input.
   - If the user did not ask for a gap scan and safe assumptions are enough, do not stop just to use this skill.

2. Check the request shape
   - Check objective (what should change vs stay the same)
   - Check done criteria (acceptance, examples, edge cases)
   - Check scope (files/components/users in or out)
   - Check constraints (compatibility, performance, style, deps, time)
   - Check environment (language/runtime versions, OS, test runner)
   - Check safety/reversibility (migrations, rollout, risk)

3. Produce the right output
   - For `gap-scan`, separate must-decide gaps from optional decisions, then propose defaults where safe.
   - For `blocking`, ask only 1 to 5 questions that remove whole branches of work.
   - Mark assumptions explicitly; do not present guessed requirements as facts.

4. Ask must-have questions first in `blocking` mode
   - Ask 1 to 5 questions that remove whole branches of work
   - Use numbered questions with short options (a/b/c)
   - Provide a clear default (bold it) and a fast path reply like "defaults"
   - Allow "not sure - use default" when helpful
   - Separate "Need to know" from "Nice to know" only if it reduces friction

5. Pause before acting only when blocked
   - Do not run commands, edit files, or make a detailed plan that depends on missing info
   - A low-risk discovery read is allowed if it does not commit to a direction

6. Confirm and proceed
   - Restate requirements and success criteria in 1 to 3 sentences
   - Begin work only after answers or explicit approval of assumptions

## Gap-Scan Format

Use this when the user explicitly asks to find missing requirements:

```text
Requirements gap scan

Must Decide
1. <decision that changes scope or correctness>
   - Suggested default: <default>
   - Why it matters: <one sentence>

Nice To Decide
- <decision that can wait or has a safe default>

Suggested Defaults
- <assumption Codex can use if the user says "defaults">

Risks
- <risk if this remains vague>

Reply with: defaults, or answer the numbered items.
```

## Blocking Format

Use a compact, scannable structure. Example:

```text
Need to know
1) Scope?
   a) **Minimal change**
   b) Refactor while touching the area
   c) Not sure - use default
2) Compatibility target?
   a) **Current project defaults**
   b) Also support older versions: <specify>
   c) Not sure - use default
Reply with: defaults (or 1a 2a)
```

## If asked to proceed without answers

- State assumptions as a short numbered list
- Ask for confirmation
- Proceed only after confirmation or corrections
