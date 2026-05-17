---
name: test-first
description: Use when the user wants implementation work governed by failing-test evidence or an explicit waiver before production code changes.
---

# Test First

## Contract

Prereqs:

- User explicitly invokes `test-first`, asks for test-first implementation mode, or asks to require failing-test evidence before production
  code changes.
- The canonical prompt source exists at `references/prompts/test-first.md`.
- Active project preflight and validation rules are followed before repository edits.

Inputs:

- Implementation task, target behavior or bug, done criteria, relevant files/modules, known test command, and constraints when available.

Outputs:

- Change classification.
- Failing-test evidence before production edits, or an explicit waiver with substitute validation.
- Scoped implementation and final validation report when the user asks for implementation.

Exit codes:

- N/A (conversation workflow; no repo scripts)

Failure modes:

- Prompt source is missing or empty.
- No usable test harness exists and the user does not accept a waiver.
- Active project rules conflict with the requested implementation path.

## Workflow

1. Read `references/prompts/test-first.md`.
2. Treat that file as the canonical prompt text for this skill invocation.
3. Run required project preflight before edits.
4. Follow the prompt's evidence, waiver, implementation, and final reporting requirements unless higher-priority instructions conflict.
