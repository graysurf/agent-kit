---
description: Make the main agent orchestrate scope and validation while subagents implement lanes.
argument-hint: goal / constraints (optional)
---

Enable **orchestrator-first mode** for this conversation thread.

GOAL / CONSTRAINTS (optional) $ARGUMENTS

POLICY (sticky for this conversation)

1. Persist for this thread
   - Treat this message as a standing instruction for the rest of the conversation thread.
   - Apply it to future user requests unless the user explicitly disables it (e.g., "orchestrator-first off").

2. Main-agent ownership
   - Main agent owns intent understanding, scope control, task decomposition, dispatch, integration, validation, and final answer.
   - Main agent should not be the primary implementer when the task can be safely delegated.
   - Main agent may make small integration or glue fixes, resolve conflicts, update coordination artifacts, or unblock stalled lanes.

3. Delegation gate
   - Dispatch implementation lanes to subagents only when the request has:
     - At least 2 independent lanes, or one broad lane that benefits from isolated implementation ownership
     - Limited file overlap
     - Clear acceptance criteria and validation
     - Straightforward integration path
   - Do not dispatch subagents for small changes, unclear requirements, tightly coupled refactors, destructive operations, or work whose
     next step blocks on the subagent result.

4. Subagent execution
   - Give each subagent a concrete task card with scope, out-of-scope items, acceptance criteria, validation, and expected artifacts.
   - Subagents own implementation inside their assigned lanes and should report files changed, validation run, and blockers.
   - The main agent reviews outputs before integrating or reporting completion.

5. Validation and reporting
   - Run the smallest meaningful validation for each lane and the best available global validation after integration.
   - Report completed lanes, blocked lanes, files changed, and validation status concisely.

On enable, respond with:

- Confirmation that orchestrator-first mode is enabled for this conversation thread.
- The delegation gate you will use.
- How to disable it ("orchestrator-first off").
