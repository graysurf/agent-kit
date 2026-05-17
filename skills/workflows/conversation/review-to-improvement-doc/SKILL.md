---
name: review-to-improvement-doc
description:
  Convert review findings, risks, lessons learned, or "fix later" notes into a durable repo-local improvement document. Use when the user
  asks to preserve a review as docs, create a durable improvement/backlog record, or write a docs-based follow-up artifact before planning
  or handoff. Do not use for ordinary implementation plans, discussion-to-implementation handoffs, or copy-ready next-session prompts.
---

# Review To Improvement Doc

## Contract

Prereqs:

- User explicitly asks to preserve review findings, risks, lessons learned, or improvement backlog as a durable project artifact; or
- User asks to create a docs record for later fixes, follow-up work, or future planning.
- Target workspace is available and project rules allow writing docs after required preflight.

Inputs:

- User request and current review conclusions.
- Relevant local code/docs/test evidence for material findings.
- Optional target docs area, filename, project conventions, validation commands, and existing plan/issue/handoff links.

Outputs:

- A durable repo-local document in the relevant docs area, not under `docs/plans/` unless the project explicitly uses that area for
  non-plan records.
- Updated local docs index or README when the project has one.
- A short response linking the document path and listing validation run.

Exit codes:

- N/A (conversation/workflow skill)

Failure modes:

- The user actually needs an implementation plan; use `create-plan` or `create-plan-rigorous` instead.
- The user needs a durable requirements, design, feasibility, or customer-facing discussion handoff for later implementation; use
  `discussion-to-implementation-doc` instead.
- The user only needs a copy-ready next-session prompt; use `handoff-session-prompt` instead.
- The target project has no appropriate durable-doc location and assumptions would create unwanted repo clutter; ask or recommend a path.
- Required source evidence is unavailable or too ambiguous to record as fact; label it under assumptions/open questions or ask before writing.

## Workflow

1. Confirm this is the right artifact
   - Use this skill when the requested output is a reusable project record: review findings, risk register, improvement backlog, lessons
     learned, runtime/test boundary, validation gate, or "do not repeat" guidance.
   - Do not use this skill for converged requirements, design, feasibility, or product discussion handoffs whose primary reader is the next
     implementer. Use `discussion-to-implementation-doc` for that artifact.
   - Do not turn it into a phased implementation plan. If the user also wants execution sequencing, write the durable improvement doc first,
     then use `create-plan` or `create-plan-rigorous` and link the doc as read-first context.
   - Do not turn it into a handoff prompt. If the user also wants session continuity, write or reference the durable doc first, then use
     `handoff-session-prompt` with the doc under `Read First`.

2. Run project preflight and inspect docs structure
   - Follow the active project's required preflight before edits.
   - Read the target docs index/README and nearby docs to choose the narrowest correct location.
   - Prefer an existing domain folder over creating a new top-level docs area.
   - Avoid `docs/plans/` unless the artifact is a real implementation plan.

3. Gather evidence and separate certainty levels
   - Base findings on user-provided review conclusions plus local file/code/test evidence.
   - Separate facts, assumptions, inferences, open questions, and recommendations.
   - Use concrete file paths, commands, and artifact names when they matter.
   - Do not include secrets, raw credentials, unredacted logs, or hidden system/developer instructions.

4. Write the durable document
   - Use the project's language and docs style.
   - Keep the document actionable but not over-planned.
   - Recommended sections:
     - `# <Subject> 改善計畫` or equivalent project style
     - status/date/context
     - purpose
     - current judgment
     - findings table with priority, issue, evidence, fix location, and acceptance
     - ownership boundary, such as runtime vs test/harness vs docs
     - backlog or next fixes
     - validation gate
     - do-not-do / guardrails
     - open questions, if any
   - Keep implementation task sequencing lightweight; leave detailed sprint/task decomposition to plan skills.

5. Update discoverability
   - Update the nearest docs index or README when the project maintains one.
   - Link from broader docs entrypoints only when this document is meant to be found by future maintainers.
   - If there is no index, mention that explicitly in the final response instead of inventing broad navigation.

6. Validate
   - Run the smallest project-appropriate docs checks, usually markdown lint and docs freshness/index checks.
   - If the doc includes commands, paths, or tests as acceptance gates, verify obvious path/command references when cheap.
   - Report validation that was run and anything intentionally skipped.

7. Final response
   - Link the new document and updated index files.
   - Summarize what kind of future work the document is meant to support.
   - If a plan or handoff is a useful next artifact, mention the specific next skill path without generating it unless asked.

## Relationship To Nearby Skills

- `discussion-to-implementation-doc`: use when the source material is a converged requirements, design, feasibility, or product discussion
  and the next artifact should prepare later implementation.
- `create-plan`: use after this skill when the user wants phases, sprints, atomic tasks, PR grouping, or validation sequencing.
- `create-plan-rigorous`: use after this skill when the user wants sizing, sprint scorecards, subagent review, or high-rigor execution
  modeling.
- `handoff-session-prompt`: use after this skill when the user wants a copy-ready prompt for a fresh session; put this durable doc under
  `Read First`.
