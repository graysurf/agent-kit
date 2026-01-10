#!/usr/bin/env -S zsh -f

if [[ -n ${_codex_psql_loaded-} ]]; then
  return 0 2>/dev/null || exit 0
fi
typeset -gr _codex_psql_loaded=1

if [[ -z "${ZSH_VERSION:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi

_codex_psql_maybe_add_libpq_path() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  command -v brew >/dev/null 2>&1 || return 0

  local libpq_prefix='' libpq_bin=''
  libpq_prefix="$(brew --prefix libpq 2>/dev/null)" || libpq_prefix=''
  libpq_bin="${libpq_prefix}/bin"
  if [[ -n $libpq_prefix && -d $libpq_bin && ":${PATH}:" != *":${libpq_bin}:"* ]]; then
    export PATH="${libpq_bin}:${PATH}"
  fi
}

codex_psql_require_env() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  local prefix='' env_file=''
  prefix="${1-}"
  env_file="${2-}"

  if [[ -z $prefix || -z $env_file ]]; then
    print -u2 -r -- "codex_psql_require_env: missing prefix/env_file"
    return 1
  fi

  if [[ ! $prefix =~ '^[A-Za-z][A-Za-z0-9_]*$' ]]; then
    print -u2 -r -- "codex_psql_require_env: invalid prefix: ${prefix}"
    return 1
  fi

  _codex_psql_maybe_add_libpq_path

  if [[ -f $env_file ]]; then
    setopt allexport
    source "$env_file"
    setopt noallexport
  fi

  local var='' value=''
  for var in "${prefix}_PGHOST" "${prefix}_PGPORT" "${prefix}_PGUSER" "${prefix}_PGPASSWORD" "${prefix}_PGDATABASE"; do
    value="${(P)var-}"
    if [[ -z $value ]]; then
      print -u2 -r -- "Missing ${var}. Check: ${env_file}"
      return 1
    fi
  done
}

codex_psql_run() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  local prefix='' env_file=''
  prefix="${1-}"
  env_file="${2-}"
  shift 2 || true

  codex_psql_require_env "$prefix" "$env_file" || return 1

  local host_var="${prefix}_PGHOST"
  local port_var="${prefix}_PGPORT"
  local user_var="${prefix}_PGUSER"
  local password_var="${prefix}_PGPASSWORD"
  local database_var="${prefix}_PGDATABASE"

  local host="${(P)host_var}"
  local port="${(P)port_var}"
  local user="${(P)user_var}"
  local password="${(P)password_var}"
  local database="${(P)database_var}"

  PGPASSWORD="$password" psql \
    --host="$host" \
    --port="$port" \
    --username="$user" \
    --dbname="$database" \
    "$@"
}
