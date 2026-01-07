# GraphQL API Test Output Template

Use this template for the `graphql-api-testing` skill.

## Output rules

- Always state the target endpoint selection (`--env <name>` / `--url <url>` / `GQL_URL=<url>`).
- Reference the exact operation/variables files used (prefer `setup/graphql/*.graphql` + `setup/graphql/*.json`).
- Include the executed command(s) in fenced `bash` blocks (do not include secrets).
- When pasting JSON (variables/response), format it in a fenced `json` block (prefer `jq -S .`).
- If generating a test report file, write it under `docs/` and include:
  - GraphQL Operation (`graphql` block)
  - Variables (`json` block, formatted)
  - Response (`json` block, formatted; redact tokens/passwords unless explicitly requested)

## Preferred report flow

- Generate a report stub (auto-fills date + formats JSON):
  - `$CODEX_HOME/skills/graphql-api-testing/scripts/gql-report.sh`
- Default output dir is `<project root>/docs`; override with `GQL_REPORT_DIR`.
