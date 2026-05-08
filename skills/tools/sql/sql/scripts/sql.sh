#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  sql.sh <postgres|mysql|mssql> --prefix <PREFIX> --env-file <path> [--query "<sql>" | --file <file.sql> | -- <client args...>]

Examples:
  sql.sh postgres --prefix TEST --env-file /dev/null --query "select 1;"
  sql.sh mysql --prefix TEST --env-file /dev/null --file ./query.sql
  sql.sh mssql --prefix TEST --env-file /dev/null -- -Q "select 1;" -h -1
USAGE
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
shared_lib="${script_dir}/../../_shared/lib/db-connect-runner.sh"
# shellcheck disable=SC1090
source "$shared_lib"

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 2
fi

dialect="${1:-}"
shift

case "$dialect" in
  postgres|mysql|mssql)
    ;;
  -h|--help|help)
    usage
    exit 0
    ;;
  *)
    echo "error: unknown SQL dialect: $dialect" >&2
    usage >&2
    exit 2
    ;;
esac

prefix=""
env_file=""
query=""
file=""
pass_args=()

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --prefix)
      prefix="${2-}"
      shift 2
      ;;
    --env-file)
      env_file="${2-}"
      shift 2
      ;;
    -q|--query)
      query="${2-}"
      shift 2
      ;;
    --file)
      file="${2-}"
      shift 2
      ;;
    --)
      shift
      pass_args+=("$@")
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: ${1:-}" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$prefix" ]]; then
  echo "error: --prefix is required" >&2
  usage >&2
  exit 2
fi
if [[ -z "$env_file" ]]; then
  echo "error: --env-file is required (use /dev/null to rely on exported env vars)" >&2
  usage >&2
  exit 2
fi
if [[ -n "$query" && -n "$file" ]]; then
  echo "error: choose only one: --query or --file" >&2
  usage >&2
  exit 2
fi
if [[ -n "$file" && ! -f "$file" ]]; then
  echo "error: missing --file: $file" >&2
  exit 2
fi

client_args=()
stdin_file=""

case "$dialect" in
  postgres)
    if [[ -n "$query" ]]; then
      client_args+=(--command "$query")
    fi
    if [[ -n "$file" ]]; then
      client_args+=(-f "$file")
    fi
    ;;
  mysql)
    if [[ -n "$query" ]]; then
      client_args+=(-e "$query")
    fi
    if [[ -n "$file" ]]; then
      stdin_file="$file"
    fi
    ;;
  mssql)
    if [[ -n "$query" ]]; then
      client_args+=(-Q "$query")
    fi
    if [[ -n "$file" ]]; then
      client_args+=(-i "$file")
    fi
    ;;
esac

if ((${#pass_args[@]})); then
  client_args+=("${pass_args[@]}")
fi

if [[ -n "$stdin_file" ]]; then
  sql_skill_run_mysql "$prefix" "$env_file" "${client_args[@]}" <"$stdin_file"
  exit $?
fi

if ((${#client_args[@]})); then
  "sql_skill_run_${dialect}" "$prefix" "$env_file" "${client_args[@]}"
else
  "sql_skill_run_${dialect}" "$prefix" "$env_file"
fi
