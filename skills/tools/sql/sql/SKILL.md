---
name: sql
description:
  Run PostgreSQL, MySQL, or SQL Server queries through one canonical SQL skill using a dialect subcommand and prefix + env file
  convention.
---

# SQL

## Contract

Prereqs:

- `bash` available on `PATH`.
- Dialect client available on `PATH`:
  - `postgres`: `psql` (the runner tries Homebrew `libpq/bin` when available)
  - `mysql`: `mysql` (the runner tries Homebrew `mysql-client/bin` when available)
  - `mssql`: `sqlcmd` (the runner tries Homebrew `mssql-tools18/bin` when available)
- Connection settings provided via exported env vars and/or an env file.

Inputs:

- Dialect subcommand: `postgres`, `mysql`, or `mssql`.
- `--prefix <PREFIX>`: env var prefix.
- `--env-file <path>`: file to `source` for env vars (use `/dev/null` to rely on already-exported env vars).
- One of:
  - `--query "<sql>"`
  - `--file <file.sql>`
  - `-- <client args...>` (pass-through to the selected client)

Outputs:

- Query results printed to stdout from the selected client; diagnostics to stderr.

Exit codes:

- `0`: success
- `2`: wrapper usage error
- non-zero: connection/auth/query error from the selected client or wrapper

Failure modes:

- Missing client binary, missing required prefixed env vars, or DB unreachable/auth failure.

## Overview

Use this canonical SQL skill for all supported database clients. Pick the dialect with the first argument:

- `postgres` uses `psql` and `<PREFIX>_PGHOST`, `<PREFIX>_PGPORT`, `<PREFIX>_PGUSER`, `<PREFIX>_PGPASSWORD`,
  `<PREFIX>_PGDATABASE`.
- `mysql` uses `mysql` and `<PREFIX>_MYSQL_HOST`, `<PREFIX>_MYSQL_PORT`, `<PREFIX>_MYSQL_USER`,
  `<PREFIX>_MYSQL_PASSWORD`, `<PREFIX>_MYSQL_DB`.
- `mssql` uses `sqlcmd` and `<PREFIX>_MSSQL_HOST`, `<PREFIX>_MSSQL_PORT`, `<PREFIX>_MSSQL_USER`,
  `<PREFIX>_MSSQL_PASSWORD`, `<PREFIX>_MSSQL_DB`.

MSSQL optional extras:

- `<PREFIX>_MSSQL_TRUST_CERT`: set to `1|true|yes` to pass `-C` to `sqlcmd`.
- `<PREFIX>_MSSQL_SCHEMA`: passed as `-v schema=<schema>` to `sqlcmd`.

Prefer read-only queries unless the user explicitly requests data changes.

## Quick Start

Run PostgreSQL:

```bash
$AGENT_HOME/skills/tools/sql/sql/scripts/sql.sh \
  postgres \
  --prefix TEST \
  --env-file /dev/null \
  --query "select 1;"
```

Run MySQL:

```bash
$AGENT_HOME/skills/tools/sql/sql/scripts/sql.sh \
  mysql \
  --prefix TEST \
  --env-file /dev/null \
  --query "select 1;"
```

Run SQL Server:

```bash
$AGENT_HOME/skills/tools/sql/sql/scripts/sql.sh \
  mssql \
  --prefix TEST \
  --env-file /dev/null \
  --query "select 1;"
```

## Safety Rules

Ask before running `UPDATE`, `DELETE`, `INSERT`, `MERGE`, `TRUNCATE`, or schema changes.

## Output and Clarification Rules

- Follow the shared template at `$AGENT_HOME/skills/tools/sql/_shared/references/ASSISTANT_RESPONSE_TEMPLATE.md`.

## Scripts (only entrypoints)

- `$AGENT_HOME/skills/tools/sql/sql/scripts/sql.sh`
