#!/usr/bin/env bash
# shellcheck disable=SC2016
set -euo pipefail

SCRIPT_NAME="setup-macos.sh"
DEFAULT_AGENT_HOME="${HOME}/.agents"
DEFAULT_CODEX_HOME="${HOME}/.codex"
DEFAULT_REPO_URL="https://github.com/graysurf/agent-kit.git"
DEFAULT_PROFILE="recommended"
MANAGED_BEGIN="# >>> agent-kit setup >>>"
MANAGED_END="# <<< agent-kit setup <<<"

PROFILE="default"
AGENT_HOME_PATH="${AGENT_KIT_AGENT_HOME:-$DEFAULT_AGENT_HOME}"
CODEX_HOME_PATH="${AGENT_KIT_CODEX_HOME:-$DEFAULT_CODEX_HOME}"
REPO_URL="${AGENT_KIT_REPO_URL:-}"
BRANCH="${AGENT_KIT_BRANCH:-}"
SKIP_BREW_UPDATE="false"
SKIP_HOMEBREW_INSTALL="false"
SKIP_COMMAND_VERIFY="false"
SKIP_HOOKS_SYNC="false"
DRY_RUN="false"

log() {
  printf 'info: %s\n' "$*" >&2
}

warn() {
  printf 'warn: %s\n' "$*" >&2
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [options]

Bootstrap or repair a macOS agent-kit workstation.

Defaults:
  --profile ${DEFAULT_PROFILE}
  --agent-home \$HOME/.agents
  --codex-home \$HOME/.codex
  --repo-url ${DEFAULT_REPO_URL}

Options:
  --profile core|recommended|full
      Select the Homebrew tool set to install.
  --agent-home PATH
      agent-kit clone/home path. Defaults to \$HOME/.agents.
  --codex-home PATH
      Codex local state path. Defaults to \$HOME/.codex.
  --repo-url URL
      agent-kit git repository URL used when --agent-home must be cloned.
  --branch NAME
      Optional branch passed to git clone and pull verification.
  --skip-brew-update
      Do not run brew update before installing/upgrading tools.
  --skip-homebrew-install
      Fail if brew is missing instead of installing Homebrew.
  --skip-command-verify
      Skip final command availability checks. Intended only for tests.
  --skip-hooks-sync
      Do not run codex-hooks-sync after writing ~/.codex/AGENTS.md.
  --dry-run
      Print the operations that would run without changing files.
  -h, --help
      Show this help.
EOF
}

run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    printf 'dry-run:' >&2
    printf ' %q' "$@" >&2
    printf '\n' >&2
    return 0
  fi
  "$@"
}

abs_path() {
  local path="$1"
  if [[ "$path" == /* ]]; then
    printf '%s\n' "$path"
  else
    printf '%s\n' "$PWD/${path#./}"
  fi
}

physical_file_path() {
  local path="$1"
  local dir base
  dir="$(dirname "$path")"
  base="$(basename "$path")"
  if [[ -d "$dir" ]]; then
    printf '%s/%s\n' "$(cd "$dir" && pwd -P)" "$base"
  else
    printf '%s\n' "$path"
  fi
}

parse_args() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --profile)
        [[ "$#" -ge 2 ]] || die "--profile requires a value"
        PROFILE="$2"
        shift 2
        ;;
      --agent-home)
        [[ "$#" -ge 2 ]] || die "--agent-home requires a value"
        AGENT_HOME_PATH="$2"
        shift 2
        ;;
      --codex-home)
        [[ "$#" -ge 2 ]] || die "--codex-home requires a value"
        CODEX_HOME_PATH="$2"
        shift 2
        ;;
      --repo-url)
        [[ "$#" -ge 2 ]] || die "--repo-url requires a value"
        REPO_URL="$2"
        shift 2
        ;;
      --branch)
        [[ "$#" -ge 2 ]] || die "--branch requires a value"
        BRANCH="$2"
        shift 2
        ;;
      --skip-brew-update)
        SKIP_BREW_UPDATE="true"
        shift
        ;;
      --skip-homebrew-install)
        SKIP_HOMEBREW_INSTALL="true"
        shift
        ;;
      --skip-command-verify)
        SKIP_COMMAND_VERIFY="true"
        shift
        ;;
      --skip-hooks-sync)
        SKIP_HOOKS_SYNC="true"
        shift
        ;;
      --dry-run)
        DRY_RUN="true"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "unsupported argument: $1"
        ;;
    esac
  done

  if [[ "$PROFILE" == "default" ]]; then
    PROFILE="$DEFAULT_PROFILE"
  fi
  case "$PROFILE" in
    core|recommended|full) ;;
    *) die "--profile must be one of: core, recommended, full" ;;
  esac

  AGENT_HOME_PATH="$(abs_path "$AGENT_HOME_PATH")"
  CODEX_HOME_PATH="$(abs_path "$CODEX_HOME_PATH")"
  if [[ -z "$REPO_URL" ]]; then
    REPO_URL="$(default_repo_url)"
  fi
}

default_repo_url() {
  local script_dir repo_root remote_url
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "${script_dir}/.." && pwd)"
  remote_url="$(git -C "$repo_root" remote get-url origin 2>/dev/null || true)"
  if [[ -n "$remote_url" ]]; then
    printf '%s\n' "$remote_url"
  else
    printf '%s\n' "$DEFAULT_REPO_URL"
  fi
}

assert_macos() {
  local uname_s
  uname_s="$(uname -s)"
  if [[ "$uname_s" == "Darwin" ]]; then
    return 0
  fi
  if [[ "${AGENT_KIT_SETUP_ASSUME_MACOS:-}" == "true" ]]; then
    warn "AGENT_KIT_SETUP_ASSUME_MACOS=true; continuing on ${uname_s} for tests"
    return 0
  fi
  die "this installer supports macOS only (found ${uname_s})"
}

install_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi
  if [[ "$SKIP_HOMEBREW_INSTALL" == "true" ]]; then
    die "brew not found and --skip-homebrew-install was set"
  fi
  log "installing Homebrew"
  if [[ "$DRY_RUN" == "true" ]]; then
    run env NONINTERACTIVE=1 CI=1 /bin/bash -c '<homebrew-install-script>'
  else
    env NONINTERACTIVE=1 CI=1 /bin/bash -c \
      "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
}

resolve_brew_bin() {
  command -v brew >/dev/null 2>&1 && command -v brew && return 0
  [[ -x /opt/homebrew/bin/brew ]] && printf '%s\n' "/opt/homebrew/bin/brew" && return 0
  [[ -x /usr/local/bin/brew ]] && printf '%s\n' "/usr/local/bin/brew" && return 0
  return 1
}

brew_prefix() {
  "$BREW_BIN" --prefix
}

brew_list_has() {
  local package="$1"
  "$BREW_BIN" list "$package" >/dev/null 2>&1
}

brew_list_has_cask() {
  local package="$1"
  "$BREW_BIN" list --cask "$package" >/dev/null 2>&1
}

brew_install_formula() {
  local package="$1"
  if brew_list_has "$package"; then
    log "brew formula already installed: ${package}"
  else
    log "installing brew formula: ${package}"
    run env HOMEBREW_NO_AUTO_UPDATE=1 "$BREW_BIN" install "$package"
  fi
}

brew_install_cask() {
  local package="$1"
  if brew_list_has_cask "$package"; then
    log "brew cask already installed: ${package}"
  else
    log "installing brew cask: ${package}"
    run env HOMEBREW_NO_AUTO_UPDATE=1 "$BREW_BIN" install --cask "$package"
  fi
}

install_nils_cli_latest() {
  log "ensuring Homebrew tap sympoies/tap"
  run env HOMEBREW_NO_AUTO_UPDATE=1 "$BREW_BIN" tap sympoies/tap

  if brew_list_has nils-cli; then
    log "upgrading nils-cli to the latest Homebrew version"
    run env HOMEBREW_NO_AUTO_UPDATE=1 "$BREW_BIN" upgrade nils-cli
  else
    log "installing nils-cli"
    run env HOMEBREW_NO_AUTO_UPDATE=1 "$BREW_BIN" install nils-cli
  fi
}

install_cli_tools() {
  local core_formulae=(
    git
    gh
    jq
    yq
    ripgrep
    fd
    fzf
    bat
    git-delta
    uv
    shellcheck
    node
    pnpm
    pipx
    direnv
  )
  local recommended_formulae=(
    tree
    eza
    glow
    xh
    httpie
    watchexec
    entr
    ruff
    ipython
    hyperfine
    lnav
    tokei
    btop
    ncdu
  )
  local full_formulae=(
    ripgrep-all
    ast-grep
    bat-extras
    repomix
    gitui
    grpcurl
    websocat
    mitmproxy
    hey
    imagemagick
    vips
    pngquant
    jpegoptim
    mozjpeg
    webp
    htop
    tailspin
    im-select
  )
  local full_casks=(
    hammerspoon
  )
  local package

  for package in "${core_formulae[@]}"; do
    brew_install_formula "$package"
  done

  if [[ "$PROFILE" == "recommended" || "$PROFILE" == "full" ]]; then
    for package in "${recommended_formulae[@]}"; do
      brew_install_formula "$package"
    done
  fi

  if [[ "$PROFILE" == "full" ]]; then
    for package in "${full_formulae[@]}"; do
      brew_install_formula "$package"
    done
    for package in "${full_casks[@]}"; do
      brew_install_cask "$package"
    done
  fi
}

ensure_agent_home() {
  if [[ ! -e "$AGENT_HOME_PATH" ]]; then
    log "cloning agent-kit into ${AGENT_HOME_PATH}"
    mkdir -p "$(dirname "$AGENT_HOME_PATH")"
    if [[ -n "$BRANCH" ]]; then
      run git clone --branch "$BRANCH" "$REPO_URL" "$AGENT_HOME_PATH"
    else
      run git clone "$REPO_URL" "$AGENT_HOME_PATH"
    fi
    return 0
  fi

  if [[ -d "$AGENT_HOME_PATH/.git" ]]; then
    mark_agents_skip_worktree || true
    local status
    status="$(git -C "$AGENT_HOME_PATH" status --porcelain --untracked-files=no 2>/dev/null || true)"
    if [[ -n "$status" ]]; then
      warn "agent-kit clone has local tracked changes; skipping git update: ${AGENT_HOME_PATH}"
      return 0
    fi
    log "updating agent-kit clone at ${AGENT_HOME_PATH}"
    run git -C "$AGENT_HOME_PATH" fetch --quiet origin
    if [[ -n "$BRANCH" ]]; then
      run git -C "$AGENT_HOME_PATH" checkout "$BRANCH"
    fi
    run git -C "$AGENT_HOME_PATH" pull --ff-only --quiet
    return 0
  fi

  if [[ -d "$AGENT_HOME_PATH" ]] && [[ -z "$(find "$AGENT_HOME_PATH" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    log "cloning agent-kit into empty directory ${AGENT_HOME_PATH}"
    if [[ -n "$BRANCH" ]]; then
      run git clone --branch "$BRANCH" "$REPO_URL" "$AGENT_HOME_PATH"
    else
      run git clone "$REPO_URL" "$AGENT_HOME_PATH"
    fi
    return 0
  fi

  die "${AGENT_HOME_PATH} exists but is not an agent-kit git clone"
}

copy_initial_codex_agents() {
  local source_agents="${AGENT_HOME_PATH}/AGENTS.md"
  local target_agents="${CODEX_HOME_PATH}/AGENTS.md"
  mkdir -p "$CODEX_HOME_PATH"

  if [[ -e "$target_agents" || -L "$target_agents" ]]; then
    materialize_codex_agents_if_needed "$source_agents" "$target_agents"
    log "Codex AGENTS.md already exists: ${target_agents}"
    return 0
  fi

  if [[ ! -f "$source_agents" ]]; then
    die "cannot initialize ${target_agents}; source missing: ${source_agents}"
  fi

  log "initializing ${target_agents} from agent-kit AGENTS.md"
  run cp "$source_agents" "$target_agents"
}

materialize_codex_agents_if_needed() {
  local source_agents="$1"
  local target_agents="$2"
  local link_target resolved_target physical_source physical_target tmp_file

  [[ -L "$target_agents" ]] || return 0
  link_target="$(readlink "$target_agents")"
  if [[ "$link_target" == /* ]]; then
    resolved_target="$link_target"
  else
    resolved_target="$(dirname "$target_agents")/${link_target}"
  fi

  physical_source="$(physical_file_path "$source_agents")"
  physical_target="$(physical_file_path "$resolved_target")"
  if [[ "$physical_source" != "$physical_target" ]]; then
    return 0
  fi

  log "materializing ${target_agents} before linking agent-kit AGENTS.md"
  tmp_file="$(mktemp)"
  run cp "$target_agents" "$tmp_file"
  run rm "$target_agents"
  run mv "$tmp_file" "$target_agents"
}

ensure_agents_symlink() {
  local source_agents="${AGENT_HOME_PATH}/AGENTS.md"
  local target_agents="${CODEX_HOME_PATH}/AGENTS.md"
  local backup_path timestamp current_target

  if [[ -L "$source_agents" ]]; then
    current_target="$(readlink "$source_agents")"
    if [[ "$current_target" == "$target_agents" ]]; then
      log "agent-kit AGENTS.md symlink already points to ${target_agents}"
      mark_agents_skip_worktree || true
      return 0
    fi
    timestamp="$(date +%Y%m%d%H%M%S)"
    backup_path="${source_agents}.agent-kit-setup-backup.${timestamp}"
    warn "backing up existing AGENTS.md symlink target ${current_target} to ${backup_path}"
    run mv "$source_agents" "$backup_path"
  elif [[ -e "$source_agents" ]]; then
    if cmp -s "$source_agents" "$target_agents"; then
      run rm "$source_agents"
    else
      timestamp="$(date +%Y%m%d%H%M%S)"
      backup_path="${source_agents}.agent-kit-setup-backup.${timestamp}"
      warn "backing up existing AGENTS.md before linking: ${backup_path}"
      run mv "$source_agents" "$backup_path"
    fi
  fi

  log "linking ${source_agents} -> ${target_agents}"
  run ln -s "$target_agents" "$source_agents"
  mark_agents_skip_worktree || true
}

mark_agents_skip_worktree() {
  if [[ ! -d "$AGENT_HOME_PATH/.git" ]]; then
    return 0
  fi
  if git -C "$AGENT_HOME_PATH" ls-files --error-unmatch AGENTS.md >/dev/null 2>&1; then
    run git -C "$AGENT_HOME_PATH" update-index --skip-worktree AGENTS.md
  fi
}

write_shell_env() {
  local zshenv="${HOME}/.zshenv"
  local tmp_file brew_path brew_prefix_value
  brew_prefix_value="$(brew_prefix)"
  brew_path="${brew_prefix_value}/bin:${brew_prefix_value}/sbin"
  mkdir -p "$(dirname "$zshenv")"
  [[ -e "$zshenv" ]] || run touch "$zshenv"
  tmp_file="$(mktemp)"

  if [[ -f "$zshenv" ]]; then
    awk -v begin="$MANAGED_BEGIN" -v end="$MANAGED_END" '
      $0 == begin { skip = 1; next }
      $0 == end { skip = 0; next }
      skip != 1 { print }
    ' "$zshenv" >"$tmp_file"
  fi

  {
    printf '%s\n' "$MANAGED_BEGIN"
    printf 'export AGENT_HOME=%q\n' "$AGENT_HOME_PATH"
    printf 'export AGENT_DOCS_HOME="$AGENT_HOME"\n'
    printf 'export PLAN_ISSUE_HOME="$AGENT_HOME"\n'
    printf 'agent_kit_brew_path=%q\n' "$brew_path"
    printf 'case ":$PATH:" in\n'
    printf '  *":$agent_kit_brew_path:"*) ;;\n'
    printf '  *) export PATH="$agent_kit_brew_path:$PATH" ;;\n'
    printf 'esac\n'
    printf 'unset agent_kit_brew_path\n'
    printf '%s\n' "$MANAGED_END"
  } >>"$tmp_file"

  log "writing managed shell env block to ${zshenv}"
  run mv "$tmp_file" "$zshenv"
}

sync_codex_hooks() {
  if [[ "$SKIP_HOOKS_SYNC" == "true" ]]; then
    log "skipping codex-hooks-sync"
    return 0
  fi
  local sync_script="${AGENT_HOME_PATH}/scripts/codex-hooks-sync"
  if [[ ! -x "$sync_script" ]]; then
    warn "codex-hooks-sync not executable; skipping: ${sync_script}"
    return 0
  fi
  local codex_parent codex_base
  codex_parent="$(dirname "$CODEX_HOME_PATH")"
  codex_base="$(basename "$CODEX_HOME_PATH")"
  if [[ "$codex_base" != ".codex" ]]; then
    warn "codex-hooks-sync only targets <home>/.codex; skipping custom codex home: ${CODEX_HOME_PATH}"
    return 0
  fi
  log "syncing Codex hook config into ${CODEX_HOME_PATH}/config.toml"
  run "$sync_script" sync --apply --home-path "$codex_parent" --agent-home "$AGENT_HOME_PATH"
}

verify_commands() {
  if [[ "$SKIP_COMMAND_VERIFY" == "true" ]]; then
    log "skipping command verification"
    return 0
  fi
  local commands=(
    agent-docs
    plan-issue
    plan-tooling
    api-rest
    api-gql
    api-grpc
    api-websocket
    api-test
    semantic-commit
    agent-out
    browser-session
    canary-check
    docs-impact
    model-cross-check
    review-evidence
    skill-usage
    test-first-evidence
    agent-scope-lock
    web-evidence
    git
    gh
    jq
    yq
    rg
    fd
    fzf
    bat
    delta
    uv
    shellcheck
    node
    pnpm
    pipx
    direnv
  )
  local recommended_commands=(
    tree
    eza
    glow
    xh
    http
    watchexec
    entr
    ruff
    ipython
    hyperfine
    lnav
    tokei
    btop
    ncdu
  )
  local command_name missing=()

  if [[ "$PROFILE" == "recommended" || "$PROFILE" == "full" ]]; then
    commands+=("${recommended_commands[@]}")
  fi

  local brew_prefix_value
  brew_prefix_value="$(brew_prefix)"
  export PATH="${brew_prefix_value}/bin:${brew_prefix_value}/sbin:${PATH}"
  for command_name in "${commands[@]}"; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      missing+=("$command_name")
    fi
  done

  if [[ "${#missing[@]}" -gt 0 ]]; then
    printf 'error: missing expected commands after setup:\n' >&2
    printf '  - %s\n' "${missing[@]}" >&2
    return 1
  fi
  log "verified expected commands for profile ${PROFILE}"
}

run_agent_docs_startup_check() {
  if [[ "$SKIP_COMMAND_VERIFY" == "true" ]]; then
    return 0
  fi
  log "running agent-docs startup check"
  run agent-docs --docs-home "$AGENT_HOME_PATH" resolve --context startup --strict --format checklist >/dev/null
}

main() {
  parse_args "$@"
  assert_macos
  install_homebrew

  BREW_BIN="$(resolve_brew_bin || true)"
  [[ -n "${BREW_BIN:-}" ]] || die "brew not found after install"
  local brew_prefix_value
  brew_prefix_value="$(brew_prefix)"
  export PATH="${brew_prefix_value}/bin:${brew_prefix_value}/sbin:${PATH}"

  if [[ "$SKIP_BREW_UPDATE" == "false" ]]; then
    log "running brew update"
    run "$BREW_BIN" update
  fi

  install_nils_cli_latest
  install_cli_tools
  ensure_agent_home
  copy_initial_codex_agents
  ensure_agents_symlink
  write_shell_env
  sync_codex_hooks
  verify_commands
  run_agent_docs_startup_check

  printf 'agent-kit setup complete\n'
  printf 'AGENT_HOME=%s\n' "$AGENT_HOME_PATH"
  printf 'CODEX_HOME=%s\n' "$CODEX_HOME_PATH"
}

main "$@"
