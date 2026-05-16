---
name: issue-follow-up
description:
  Use when the user wants to open or continue a GitHub issue as the durable timeline for a discovered problem,
  investigation, blocker, implementation handoff, or unresolved follow-up loop.
---

# Issue Follow-Up

Issue-centered entrypoint for turning discovered problems into GitHub issue timelines and continuing work through comments,
implementation handoff, PRs, and closure.

## Contract

Prereqs:

- Run inside the target GitHub-backed git repo.
- `gh` available on `PATH`, and `gh auth status` succeeds.
- `issue-lifecycle` is available for issue mutations.
- Existing issue number or URL is known for follow-up mode; otherwise use open mode.
- For implementation handoff, the appropriate implementation or PR workflow is available.

Inputs:

- New problem report, observation, screenshot/path, source evidence, or user instruction to open a tracking issue.
- Existing issue number or URL plus a request to continue, investigate, update, unblock, implement, or close.
- Optional desired state: `comment-only`, `blocked`, `ready-for-implementation`, `implemented-via-pr`, or `close`.

Outputs:

- New GitHub issue URL, or a concise follow-up comment posted to the existing issue.
- A normalized checkpoint recording what was checked, what changed, the current decision, and next action.
- If implementation is appropriate: handoff into the normal implementation/PR workflow with issue traceability preserved.
- If unresolved: issue remains open with the blocker or next follow-up action recorded.

Exit codes:

- N/A (conversation workflow; underlying `issue-lifecycle`, `gh`, git, or PR workflow command failures surface directly).

Failure modes:

- Missing or ambiguous target issue in follow-up mode.
- `gh` auth, permission, network, or repository context failure.
- Required evidence cannot be accessed and no safe summary can be recorded.
- User asks to inline a local image but no GitHub-hosted attachment/URL is available.
- Implementation is ready but branch, PR, test, or delivery workflow requirements are unclear or blocked.

## Role

Use this skill as a routing layer, not as a replacement for lower-level issue or PR tools.

- Use `issue-lifecycle` for open, update, comment, close, and reopen operations.
- Use normal implementation and PR workflows when code/docs changes are ready.
- Use `issue-pr-review` when PR review decisions or review follow-up must be mirrored back to the issue.
- Use `issue-delivery` only for heavyweight plan/subagent/close-gate issue execution.

## Modes

### Open Mode

Use when the user discovered a problem and wants a tracking issue.

1. Normalize the problem into:
   - summary
   - current behavior
   - expected behavior or desired outcome
   - evidence checked
   - next investigation or implementation path
2. Include screenshots as GitHub-renderable links when a URL is available.
   - If only a local screenshot path is available, include the path plus a short visual summary.
   - Do not create unrelated repo artifacts just to host an image unless the user asks.
3. Open the issue with `issue-lifecycle`:

   ```bash
   $AGENT_HOME/skills/workflows/issue/issue-lifecycle/scripts/manage_issue_lifecycle.sh open \
     --title "<issue title>" \
     --body-file "<body.md>" \
     --label issue
   ```

4. Report the issue URL and whether any evidence could not be embedded.

### Follow-Up Mode

Use when an issue already exists and the user asks to continue it.

1. Read the issue body and comments before deciding the next action:

   ```bash
   gh issue view <issue> --json number,title,state,body,comments,labels,url
   ```

2. Identify the latest checkpoint, open questions, blockers, linked PRs, and current expected next action.
3. Do the requested investigation or maintenance work.
4. Post one concise issue comment for every meaningful follow-up unless the user explicitly asks not to write to GitHub.
5. Use this checkpoint shape:

   ```markdown
   ## Follow-up YYYY-MM-DD

   ### Checked
   - ...

   ### Result
   - ...

   ### Decision
   - comment-only | blocked | ready-for-implementation | implemented-via-pr | close

   ### Next
   - ...
   ```

6. Keep unresolved issues open. Close only when the requested outcome is complete or the user explicitly chooses not to continue.

### Implementation Handoff

Use when follow-up determines the issue is actionable.

1. Record the decision in the issue first or as part of the PR linkage comment.
2. Enter the appropriate implementation workflow for the repo and provider.
3. Keep the issue as the durable timeline:
   - link PR URLs
   - summarize tests
   - record blockers
   - mirror review follow-up decisions
   - record merge/close outcome
4. If implementation fails or is blocked, comment on the issue with the exact unblock action and leave it open.

## Comment Discipline

- Keep comments concise and evidence-based.
- Do not paste long logs; summarize and link to durable artifacts when available.
- Separate facts, inferences, blockers, and next actions when the state is uncertain.
- Do not let chat history become the only source of truth once an issue exists.
- Avoid opening replacement issues for the same unresolved problem unless the user explicitly wants a split.
