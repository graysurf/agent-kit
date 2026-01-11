---
name: qb-mysql
description: Run MySQL queries via the repo-local qb-mysql wrapper. Use when the user asks to query the QB MySQL database, inspect schemas/tables/columns, or execute SQL via qb-mysql/mysql using the QB_MYSQL_* environment.
---

# Qb-mysql

## Contract

Prereqs:
- `mysql` client available on `PATH`.
- Wrapper loaded: `source $CODEX_HOME/skills/_projects/qburger/scripts/qb-mysql.zsh`.
- `QB_MYSQL_*` values configured in `$CODEX_HOME/skills/_projects/qburger/qb-mysql.env`.

Inputs:
- SQL via `qb-mysql -e "<sql>"` or stdin redirection (`qb-mysql < file.sql`).
- Optional `mysql` flags passed through to `mysql`.

Outputs:
- Query results printed to stdout.
- Errors and diagnostics printed to stderr.

Exit codes:
- `0`: success
- non-zero: connection/auth/query error (from `mysql`)

Failure modes:
- Wrapper function not loaded (run the `source .../qb-mysql.zsh` step).
- Missing/invalid `QB_MYSQL_*` env values (auth/connection failure).
- DB unreachable (network/VPN/DNS/firewall).

## Overview

Use qb-mysql to run mysql against the QB database using the values in `$CODEX_HOME/skills/_projects/qburger/qb-mysql.env`. Favor read-only queries unless the user explicitly requests data changes.

## Quick Start

1) Ensure the function is available.

```
source $CODEX_HOME/skills/_projects/qburger/scripts/qb-mysql.zsh
```

2) Run a query.

```
qb-mysql -e "SELECT 1;"
```

3) Run a file.

```
qb-mysql < /path/to/query.sql
```

## Verification Checks

Run a lightweight query to confirm connectivity and basic output.

```
qb-mysql -e "SELECT DATABASE();"
```

If the function is missing, source the wrapper again. If the connection fails, verify that all `QB_MYSQL_*` values exist in `$CODEX_HOME/skills/_projects/qburger/qb-mysql.env`.

## Safety Rules

Ask before running `UPDATE`, `DELETE`, `INSERT`, `TRUNCATE`, or schema changes.
If a column or table name is unknown, inspect schema first with `information_schema` or `DESCRIBE`.
Do not print secrets from `.env` or echo `QB_MYSQL_PASSWORD`.

## Output and clarification rules

- Follow the shared template at `$CODEX_HOME/docs/templates/SQL_OUTPUT_TEMPLATE.md`.
