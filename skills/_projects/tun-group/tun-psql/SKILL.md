---
name: tun-psql
description: Run PostgreSQL queries via the repo-local tun-psql wrapper. Use when the user asks to query the TUN Postgres database, inspect schemas/tables/columns, or execute SQL via tun-psql/psql using the TUN_PG* environment.
---

# Tun-psql

## Overview

Use tun-psql to run psql against the TUN database using the values in `$CODEX_HOME/skills/_projects/tun-group/tun-psql.env`. Favor read-only queries unless the user explicitly requests data changes.

## Quick Start

1) Ensure the function is available.

```
source $CODEX_HOME/skills/_projects/tun-group/scripts/tun-psql.zsh
```

2) Run a query.

```
tun-psql -c "SELECT 1;"
```

3) Run a file.

```
tun-psql -f /path/to/query.sql
```

## Verification Checks

Run a lightweight query to confirm connectivity and basic output.

```
tun-psql -c "SELECT current_database();"
```

If the function is missing, source the wrapper again. If the connection fails, verify that all `TUN_PG*` values exist in `$CODEX_HOME/skills/_projects/tun-group/tun-psql.env`.

## Safety Rules

Ask before running `UPDATE`, `DELETE`, `INSERT`, `TRUNCATE`, or schema changes.
If a column or table name is unknown, inspect schema first with `information_schema` or `\d+`.
Do not print secrets from `.env` or echo `TUN_PGPASSWORD`.

## Output and clarification rules

- Follow the shared template at `$CODEX_HOME/docs/templates/SQL_OUTPUT_TEMPLATE.md`.
