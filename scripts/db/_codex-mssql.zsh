#!/usr/bin/env -S zsh -f

if [[ -n ${_codex_mssql_loaded-} ]]; then
  return 0 2>/dev/null || exit 0
fi
typeset -gr _codex_mssql_loaded=1

if [[ -z "${ZSH_VERSION:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi

_codex_mssql_maybe_add_sqlcmd_path() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  command -v sqlcmd >/dev/null 2>&1 && return 0
  command -v brew >/dev/null 2>&1 || return 0

  local mssql_tools_prefix='' mssql_tools_bin=''
  mssql_tools_prefix="$(brew --prefix mssql-tools18 2>/dev/null)" || mssql_tools_prefix=''
  mssql_tools_bin="${mssql_tools_prefix}/bin"
  if [[ -n $mssql_tools_prefix && -d $mssql_tools_bin && ":${PATH}:" != *":${mssql_tools_bin}:"* ]]; then
    export PATH="${mssql_tools_bin}:${PATH}"
  fi
}

codex_mssql_require_env() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  local prefix='' env_file=''
  prefix="${1-}"
  env_file="${2-}"

  if [[ -z $prefix || -z $env_file ]]; then
    print -u2 -r -- "codex_mssql_require_env: missing prefix/env_file"
    return 1
  fi

  if [[ ! $prefix =~ '^[A-Za-z][A-Za-z0-9_]*$' ]]; then
    print -u2 -r -- "codex_mssql_require_env: invalid prefix: ${prefix}"
    return 1
  fi

  _codex_mssql_maybe_add_sqlcmd_path

  if [[ -f $env_file ]]; then
    setopt allexport
    source "$env_file"
    setopt noallexport
  fi

  local var='' value=''
  for var in "${prefix}_MSSQL_HOST" "${prefix}_MSSQL_PORT" "${prefix}_MSSQL_USER" "${prefix}_MSSQL_PASSWORD" "${prefix}_MSSQL_DB"; do
    value="${(P)var-}"
    if [[ -z $value ]]; then
      print -u2 -r -- "Missing ${var}. Check: ${env_file}"
      return 1
    fi
  done
}

codex_mssql_run() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  local prefix='' env_file=''
  prefix="${1-}"
  env_file="${2-}"
  shift 2 || true

  codex_mssql_require_env "$prefix" "$env_file" || return 1

  local host_var="${prefix}_MSSQL_HOST"
  local port_var="${prefix}_MSSQL_PORT"
  local user_var="${prefix}_MSSQL_USER"
  local password_var="${prefix}_MSSQL_PASSWORD"
  local database_var="${prefix}_MSSQL_DB"
  local trust_cert_var="${prefix}_MSSQL_TRUST_CERT"
  local schema_var="${prefix}_MSSQL_SCHEMA"

  local host="${(P)host_var}"
  local port="${(P)port_var}"
  local user="${(P)user_var}"
  local password="${(P)password_var}"
  local database="${(P)database_var}"
  local trust_cert="${(P)trust_cert_var-}"
  local schema="${(P)schema_var-}"

  local server="${host},${port}"
  local -a base_args=()

  base_args=(
    -S "$server"
    -U "$user"
    -P "$password"
    -d "$database"
  )

  if [[ -n $schema ]]; then
    base_args+=(-v "schema=${schema}")
  fi

  case ${trust_cert:l} in
    1|true|yes)
      base_args+=("-C")
      ;;
  esac

  sqlcmd "${base_args[@]}" "$@"
}
