---
name: actionable-advice
description: Use when the user asks for actionable engineering advice with clarifying questions, options, tradeoffs, assumptions, and one recommendation.
---

# Actionable Advice

## Contract

Prereqs:

- User explicitly invokes `actionable-advice`, asks to use this prompt-style skill, or asks for structured actionable advice rather than
  implementation.
- The canonical prompt source exists at `references/prompts/actionable-advice.md`.

Inputs:

- User question and any supplied context, constraints, environment details, or done criteria.
- Optional inline argument text to treat as the user question.

Outputs:

- A concise answer shaped by the canonical prompt source.
- Clarifying questions only when critical context is missing.
- No repo file changes, command execution, or durable artifacts unless the user separately asks for them.

Exit codes:

- N/A (conversation workflow; no repo scripts)

Failure modes:

- Prompt source is missing or empty.
- The request is actually implementation, validation, delivery, or repository maintenance work; follow the active project workflow instead.
- Critical context is missing and no safe assumptions are available.

## Workflow

1. Read `references/prompts/actionable-advice.md`.
2. Treat that file as the canonical prompt text for this skill invocation.
3. Replace `$ARGUMENTS` conceptually with the current user question and available context.
4. Follow the prompt shape unless higher-priority system, developer, user, or project instructions conflict.
