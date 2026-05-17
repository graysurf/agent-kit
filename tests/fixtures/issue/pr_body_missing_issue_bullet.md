## Summary

- Implement fixture workflow behavior for issue-driven PR checks.

## Scope

- Update validation scripts and issue-body handling.
- Keep orchestration roles explicit.

## Test-First Evidence

- Change classification: workflow validator behavior.
- Failing test before fix: tests/workflows/issue/test_pr_body_schema.py::test_requires_issue_bullet failed before implementation.
- Final validation: scripts/test.sh -m script_smoke -k issue (pass).
- Waiver reason: N/A.

## Testing

- scripts/test.sh -m script_smoke -k issue (pass)

## Issue

- See related issue in commit log.
