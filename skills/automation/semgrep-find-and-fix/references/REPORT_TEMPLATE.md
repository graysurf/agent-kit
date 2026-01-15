# Semgrep Findings Report

Generated: <YYYY-MM-DD>
Repo: <org/repo or local path>

## Scan Details

- Semgrep version: `<semgrep --version>`
- Config entrypoint: `<path>`
- Command: `semgrep scan --config "<path>" --json --metrics=off --disable-version-check .`

## Summary

- Findings: <count>
- Errors: <count> (parsing / scan failures, if any)

## Top Findings

| Rule ID | Severity | Confidence | Location | Message | Suggested Next Step |
| --- | --- | --- | --- | --- | --- |
| <rule.id> | error\|warning\|info | high\|medium\|low\|unknown | <path:line> | <short> | <fix or suppress> |

## Notes

- Prefer config-layer suppression (`.semgrepignore`, config `paths`, disable low-value rules) over adding `nosem` to code.
