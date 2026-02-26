# Duck Loop Fixtures

This folder is test-only and disposable. It exists to validate plan-issue
runtime behavior and should not be treated as production data.

## Execution Profile Matrix

| execution-profile | Purpose | Sprint usage |
| --- | --- | --- |
| per-sprint | One shared PR group for all tasks in a sprint | Sprint 1 baseline |
| group-shared | Mixed grouping with a shared group lane | Sprint 2 fixtures |
| group-isolated | One isolated group per task | Sprint 3 fixtures |

## Layout

- `sprint1/per-sprint/`: Sprint 1 baseline fixtures.
- `sprint2/group-shared/`: Group-mode shared and isolated pairing fixtures.
- `sprint3/group-isolated/`: Group-mode isolated fixtures.
