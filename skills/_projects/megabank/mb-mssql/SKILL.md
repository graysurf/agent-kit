---
name: mb-mssql
description: Run SQL Server queries via the repo-local mb-mssql wrapper. Use when the user asks to query the MB database, inspect schemas/tables/columns, or execute SQL via mb-mssql/sqlcmd using the MB_MSSQL_* environment.
---

# Mb-mssql

## Overview

Use mb-mssql to run sqlcmd against the MB database using the values in `$CODEX_HOME/skills/_projects/megabank/mb-mssql.env`. Favor read-only queries unless the user explicitly requests data changes.

## Quick Start

1) Ensure the function is available.

```
source $CODEX_HOME/skills/_projects/megabank/scripts/mb-mssql.zsh
```

2) Run a query.

```
mb-mssql -Q "SELECT 1;"
```

3) Run a file.

```
mb-mssql -i /path/to/query.sql
```

## Verification Checks

Run a lightweight query to confirm connectivity and basic output.

```
mb-mssql -Q "SELECT DB_NAME();"
```

If the function is missing, source the wrapper again. If the connection fails, verify that all `MB_MSSQL_*` values exist in `$CODEX_HOME/skills/_projects/megabank/mb-mssql.env`.

## Safety Rules

Ask before running `UPDATE`, `DELETE`, `INSERT`, `MERGE`, `TRUNCATE`, or schema changes.
If a schema, table, or column name is unknown, inspect `INFORMATION_SCHEMA` first.
Do not print secrets from `.env` or echo `MB_MSSQL_PASSWORD`.

## Output and clarification rules

- Follow the shared template at `$CODEX_HOME/docs/templates/SQL_OUTPUT_TEMPLATE.md`.
