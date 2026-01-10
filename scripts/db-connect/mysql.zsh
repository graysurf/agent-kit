#!/usr/bin/env -S zsh -f

if [[ -n ${_codex_mysql_loaded-} ]]; then
  return 0 2>/dev/null || exit 0
fi
typeset -gr _codex_mysql_loaded=1

if [[ -z "${ZSH_VERSION:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi

_codex_mysql_maybe_add_mysql_client_path() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  command -v mysql >/dev/null 2>&1 && return 0
  command -v brew >/dev/null 2>&1 || return 0

  local mysql_client_prefix='' mysql_client_bin=''
  mysql_client_prefix="$(brew --prefix mysql-client 2>/dev/null)" || mysql_client_prefix=''
  mysql_client_bin="${mysql_client_prefix}/bin"
  if [[ -n $mysql_client_prefix && -d $mysql_client_bin && ":${PATH}:" != *":${mysql_client_bin}:"* ]]; then
    export PATH="${mysql_client_bin}:${PATH}"
  fi
}

codex_mysql_require_env() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  local prefix='' env_file=''
  prefix="${1-}"
  env_file="${2-}"

  if [[ -z $prefix || -z $env_file ]]; then
    print -u2 -r -- "codex_mysql_require_env: missing prefix/env_file"
    return 1
  fi

  if [[ ! $prefix =~ '^[A-Za-z][A-Za-z0-9_]*$' ]]; then
    print -u2 -r -- "codex_mysql_require_env: invalid prefix: ${prefix}"
    return 1
  fi

  _codex_mysql_maybe_add_mysql_client_path

  if [[ -f $env_file ]]; then
    setopt allexport
    source "$env_file"
    setopt noallexport
  fi

  local var='' value=''
  for var in "${prefix}_MYSQL_HOST" "${prefix}_MYSQL_PORT" "${prefix}_MYSQL_USER" "${prefix}_MYSQL_PASSWORD" "${prefix}_MYSQL_DB"; do
    value="${(P)var-}"
    if [[ -z $value ]]; then
      print -u2 -r -- "Missing ${var}. Check: ${env_file}"
      return 1
    fi
  done
}

codex_mysql_run() {
  emulate -L zsh
  setopt localoptions pipe_fail nounset

  local prefix='' env_file=''
  prefix="${1-}"
  env_file="${2-}"
  shift 2 || true

  codex_mysql_require_env "$prefix" "$env_file" || return 1

  local host_var="${prefix}_MYSQL_HOST"
  local port_var="${prefix}_MYSQL_PORT"
  local user_var="${prefix}_MYSQL_USER"
  local password_var="${prefix}_MYSQL_PASSWORD"
  local database_var="${prefix}_MYSQL_DB"

  local host="${(P)host_var}"
  local port="${(P)port_var}"
  local user="${(P)user_var}"
  local password="${(P)password_var}"
  local database="${(P)database_var}"

  MYSQL_PWD="$password" mysql \
    --protocol=tcp \
    --host="$host" \
    --port="$port" \
    --user="$user" \
    "$database" \
    "$@" \
    -A
}
