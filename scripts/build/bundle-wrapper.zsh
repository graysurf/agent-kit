#!/usr/bin/env -S zsh -f
# Bundle a wrapper script into a single standalone command by inlining sources.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  bundle-wrapper.zsh --input <wrapper> --output <path> [--entry <fn>]

Notes:
  - Bundles a wrapper script by inlining its sourced files.
  - Only supports simple "source" lines and a "sources=(...)" array pattern.
  - Expects ZDOTDIR-style paths; will set defaults if missing.
USAGE
}

die() {
  print -u2 -r -- "error: $*"
  exit 1
}

input=""
output=""
entry=""

while [[ $# -gt 0 ]]; do
  case "${1-}" in
    --input)
      input="${2-}"
      shift 2
      ;;
    --output)
      output="${2-}"
      shift 2
      ;;
    --entry)
      entry="${2-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: ${1-}"
      ;;
  esac
done

[[ -n "$input" ]] || die "--input is required"
[[ -n "$output" ]] || die "--output is required"
[[ -f "$input" ]] || die "input not found: $input"

typeset -g ZDOTDIR="${ZDOTDIR:-$HOME/.config/zsh}"
export ZDOTDIR
export ZSH_CONFIG_DIR="${ZSH_CONFIG_DIR:-$ZDOTDIR/config}"
export ZSH_BOOTSTRAP_SCRIPT_DIR="${ZSH_BOOTSTRAP_SCRIPT_DIR:-$ZDOTDIR/bootstrap}"
export ZSH_SCRIPT_DIR="${ZSH_SCRIPT_DIR:-$ZDOTDIR/scripts}"

for var in ZSH_CONFIG_DIR ZSH_BOOTSTRAP_SCRIPT_DIR ZSH_SCRIPT_DIR; do
  if [[ -z "${(P)var-}" ]]; then
    die "missing env: $var"
  fi
done

print -u2 -r -- "bundle: input=$input"
print -u2 -r -- "bundle: output=$output"
print -u2 -r -- "bundle: ZDOTDIR=$ZDOTDIR"
print -u2 -r -- "bundle: ZSH_CONFIG_DIR=$ZSH_CONFIG_DIR"
print -u2 -r -- "bundle: ZSH_BOOTSTRAP_SCRIPT_DIR=$ZSH_BOOTSTRAP_SCRIPT_DIR"
print -u2 -r -- "bundle: ZSH_SCRIPT_DIR=$ZSH_SCRIPT_DIR"

typeset -a sources_from_array=()
typeset -a sources_explicit=()
typeset -A seen_sources=()

add_source() {
  local path="$1"
  [[ -z "$path" ]] && return 0
  if [[ ! -f "$path" ]]; then
    die "source file not found: $path"
  fi
  if (( ${+seen_sources[$path]} )); then
    return 0
  fi
  seen_sources[$path]=1
  sources_explicit+=("$path")
}

parse_sources_array() {
  local file="$1"
  local in_sources=0
  local line=""
  while IFS= read -r line; do
    if [[ "$line" == *"typeset -a sources=("* ]]; then
      in_sources=1
      continue
    fi
    if (( in_sources )); then
      if [[ "$line" == *")"* ]]; then
        in_sources=0
        continue
      fi
      if [[ "$line" =~ '"([^"]+)"' ]]; then
        sources_from_array+=("${match[1]}")
      fi
    fi
  done < "$file"
}

parse_explicit_sources() {
  local file="$1"
  local line=""
  local dir="${file:h}"
  local -a tokens=()
  while IFS= read -r line; do
    [[ "$line" == *"source "* || "$line" == *". "* ]] || continue
    tokens=(${(z)line})
    [[ ${#tokens[@]} -ge 2 ]] || continue
    if [[ "${tokens[1]}" != "source" && "${tokens[1]}" != "." ]]; then
      continue
    fi
    local raw="${tokens[2]}"
    if [[ "$raw" == *'$('* || "$raw" == *'`'* || "$raw" == *'<('* ]]; then
      die "dynamic source unsupported: $raw"
    fi
    if [[ "$raw" == *'$src'* || "$raw" == *'${src}'* ]]; then
      continue
    fi
    local expanded=""
    eval "expanded=${raw}"
    expanded="${expanded/#\~/$HOME}"
    if [[ "$expanded" != /* ]]; then
      expanded="${dir%/}/${expanded}"
    fi
    add_source "$expanded"
  done < "$file"
}

parse_sources_array "$input"
parse_explicit_sources "$input"

typeset -a all_sources=("${sources_explicit[@]}")
for src in "${sources_from_array[@]}"; do
  add_source "${ZSH_SCRIPT_DIR%/}/$src"
done
all_sources=("${sources_explicit[@]}")

tmpfile="$(mktemp 2>/dev/null || true)"
[[ -n "$tmpfile" ]] || die "failed to create temp file"

{
  local input_label="$input"
  if [[ "$input_label" == "$HOME/"* ]]; then
    input_label="~/${input_label#$HOME/}"
  fi

  print -r -- "#!/usr/bin/env -S zsh -f"
  print -r -- "set -e"
  print -r -- ""
  print -r -- "# Bundled from: ${input_label}"
  print -r -- ': "${ZDOTDIR:=$HOME/.config/zsh}"'
  print -r -- "export ZDOTDIR"
  print -r -- 'export ZSH_CONFIG_DIR="${ZSH_CONFIG_DIR:-$ZDOTDIR/config}"'
  print -r -- 'export ZSH_BOOTSTRAP_SCRIPT_DIR="${ZSH_BOOTSTRAP_SCRIPT_DIR:-$ZDOTDIR/bootstrap}"'
  print -r -- 'export ZSH_SCRIPT_DIR="${ZSH_SCRIPT_DIR:-$ZDOTDIR/scripts}"'
  print -r -- ""

  local src=""
  local label=""
  for src in "${all_sources[@]}"; do
    label="$src"
    if [[ "$label" == "$ZSH_SCRIPT_DIR/"* ]]; then
      label="${label#$ZSH_SCRIPT_DIR/}"
    elif [[ "$label" == "$HOME/"* ]]; then
      label="~/${label#$HOME/}"
    fi
    print -r -- "# --- BEGIN ${label}"
    cat "$src"
    print -r -- ""
    print -r -- "# --- END ${label}"
    print -r -- ""
  done

  if [[ -n "$entry" ]]; then
    print -r -- "if ! typeset -f ${entry} >/dev/null 2>&1; then"
    print -r -- "  print -u2 -r -- \"❌ missing function: ${entry}\""
    print -r -- "  exit 1"
    print -r -- "fi"
    print -r -- ""
    print -r -- "${entry} \"\$@\""
  fi
} > "$tmpfile"

mkdir -p -- "${output:h}"
mv -f "$tmpfile" "$output"
chmod +x "$output"
