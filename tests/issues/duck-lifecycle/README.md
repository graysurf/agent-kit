# Duck Lifecycle Test Fixtures

This `tests/issues/duck-lifecycle` area is a disposable workspace for
issue-`#175` lifecycle fixture testing.

- Scope: test-only markdown fixtures used by plan-issue lifecycle flows.
- Safety: PR-safe because files are isolated under this disposable directory.
- Layout: `sprint1/serial/step-a.md` and `sprint1/serial/step-b.md` cover the
  serial lane chain for Sprint 1.
- Cleanup: run the command documented in `CLEANUP.md` to remove the workspace.
