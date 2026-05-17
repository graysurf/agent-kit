---
name: discussion-to-implementation-doc
description:
  Convert completed requirements, design, feasibility, or customer-facing discussion into a durable implementation-readiness document.
---

# Discussion To Implementation Doc

Use this skill after a discussion has converged and the next useful artifact is a repo-local document that future implementation can read.

## Contract

Prereqs:

- User wants to preserve discussion conclusions for later implementation, not execute the implementation now.
- Discussion context is sufficient to separate confirmed facts, decisions, assumptions, open questions, and recommendations.
- Target workspace is available and project rules allow writing docs after required preflight.

Inputs:

- User request and the discussion conclusions to preserve.
- Relevant local code, docs, issue, ticket, test, or runtime evidence for material facts when available.
- Optional target docs area, filename, linked issue/plan/handoff, validation commands, and project-specific documentation conventions.

Outputs:

- A durable repo-local implementation-readiness document in the relevant docs area, not under `docs/plans/` unless the project explicitly
  uses that area for non-plan handoff records.
- Updated local docs index or README when the project has one and the new document should be discoverable.
- A short response linking the document path and listing validation run.

Exit codes:

- N/A (conversation/workflow skill)

Failure modes:

- The user actually needs phased tasks, sprint grouping, PR splitting, or detailed execution sequencing; use `create-plan` or
  `create-plan-rigorous` instead.
- The user only needs a copy-ready prompt for a fresh session; use `handoff-session-prompt` instead.
- The user wants to preserve review findings, risk register entries, lessons learned, or fix-later backlog; use
  `review-to-improvement-doc` instead.
- Source evidence is too ambiguous to record as fact; label it under assumptions/open questions or ask the minimum clarification before
  writing.

## Workflow

1. Confirm this is the right artifact
   - Use this skill when requirements, design, feasibility, architecture, customer-facing, or product discussion has converged and the next
     implementer needs a stable read-first document.
   - Do not turn the document into a task-by-task implementation plan. If execution sequencing is needed, write this document first, then use
     `create-plan` and link this document as read-first context.
   - Do not use the document as a session prompt. If continuity is needed, write or reference this document first, then use
     `handoff-session-prompt`.
   - Do not use `review-evidence` as the primary artifact for this workflow. If review findings or validation records matter, attach or link
     those evidence files from the document.

2. Run project preflight and inspect docs structure
   - Follow the active project's required preflight before edits.
   - Read the target docs index, nearby docs, and local project rules before choosing a path.
   - Prefer an existing domain docs folder over creating a new top-level docs area.
   - Avoid `docs/plans/` unless the artifact is explicitly an implementation plan or the project defines another convention.

3. Gather and classify discussion content
   - Separate confirmed facts, decisions, assumptions, inferences, recommendations, open questions, and constraints.
   - Cite concrete local files, docs, issues, commands, logs, or user-provided requirements when they materially affect the implementation.
   - Preserve scope and non-scope explicitly.
   - Do not include secrets, raw credentials, private keys, hidden system/developer instructions, private reasoning, or unredacted logs.

4. Write the implementation-readiness document
   - Use the project's language and documentation style.
   - Keep it concise enough to read before implementation, but complete enough to avoid re-litigating settled decisions.
   - Recommended sections:
     - `# <Subject> Implementation Handoff`
     - status, date, source, and intended next step
     - purpose
     - confirmed facts
     - decisions
     - scope
     - non-scope
     - implementation boundaries
     - requirements
     - acceptance criteria
     - validation plan
     - risks and guardrails
     - open questions
     - read-first references
     - recommended next artifact

5. Update discoverability
   - Update the nearest docs index or README when the project maintains one.
   - Link from broader docs entrypoints only when future maintainers should find the document without prior session context.
   - If no index exists, mention that in the final response rather than inventing broad navigation.

6. Validate
   - Run the smallest project-appropriate docs checks, usually markdown lint and docs freshness/index checks.
   - If the document names commands, files, tests, or runtime gates as acceptance criteria, verify obvious references when cheap.
   - Report validation that was run and anything intentionally skipped.

## Relationship To Nearby Skills

- `review-evidence`: use for normalized review findings and validation records; link it from this document when evidence matters.
- `review-to-improvement-doc`: use when the durable artifact is a review finding, improvement backlog, risk register, or fix-later record.
- `create-plan`: use after this skill when implementation needs phases, tasks, ownership lanes, PR grouping, or validation sequencing.
- `handoff-session-prompt`: use after this skill when the user wants a copy-ready prompt for a fresh session; put this document under
  `Read First`.
