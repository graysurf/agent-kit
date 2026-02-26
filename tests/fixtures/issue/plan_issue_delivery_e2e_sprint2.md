# Plan-Issue-Delivery E2E Fixture (Sprint 2)

## Task Decomposition

| Task ID | Summary | Owner | Execution Lane | PR | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| S2T1 | Extend runbook with Sprint 2 gating checklist | subagent-s2-t1 | pr-shared:sprint2-shared-a | #201 | done | Shared lane anchor row after canonical normalization. |
| S2T2 | Add Sprint 2 fixture for normalized PR and done-state sync | subagent-s2-t1 | pr-shared:sprint2-shared-a | #201 | done | `link-pr --task` sync keeps grouped row status aligned to lane anchor. |
| S2T3 | Add regression test for normalization and done-state invariants | subagent-s2-t1 | pr-shared:sprint2-shared-b | #202 | done | Secondary grouped lane demonstrates independent shared PR normalization. |
| S2T4 | Add sprint-review transcript template for main-agent review | subagent-s2-t1 | pr-shared:sprint2-shared-b | #202 | done | Sprint-level `accept-sprint` gate requires merged PR before done-state persists. |

## Sprint 2 Gate Snapshot

- Grouped lane behavior is explicit via `pr-shared:*` execution lanes.
- Canonical PR references are represented as `#201` and `#202`.
- Sprint acceptance invariants are represented with `done` status for each lane row.
