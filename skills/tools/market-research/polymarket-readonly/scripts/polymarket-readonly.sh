#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  polymarket-readonly.sh --check-env
  polymarket-readonly.sh --print-codex-config
  polymarket-readonly.sh --smoke [--limit <n>]
  polymarket-readonly.sh --search <query> [--limit <n>]
  polymarket-readonly.sh --help

Read-only Polymarket helper. It never uses private keys or authenticated trading
credentials. --smoke checks a public Gamma API endpoint only. --search uses the
Gamma public-search REST fallback with the current q= parameter.
USAGE
}

limit=1
mode=""
search_query=""

unsafe_env_names=(
  POLYMARKET_PRIVATE_KEY
  POLYMARKET_API_KEY
  POLYMARKET_API_SECRET
  POLYMARKET_API_PASSPHRASE
  POLYMARKET_BUILDER_API_KEY
  POLYMARKET_BUILDER_API_SECRET
  POLYMARKET_BUILDER_API_PASSPHRASE
  POLYMARKET_BUILDER_AUTH_HEADER
)

check_env() {
  local found=()
  local name
  for name in "${unsafe_env_names[@]}"; do
    if [[ -n "${!name:-}" ]]; then
      found+=("$name")
    fi
  done

  if [[ ${#found[@]} -gt 0 ]]; then
    printf 'error: unsafe Polymarket trading credential env present: %s\n' "${found[*]}" >&2
    return 3
  fi
}

print_codex_config() {
  cat <<'CONFIG'
[mcp_servers.polymarket]
command = "/Users/terry/.local/bin/uvx"
args = ["--from", "polymarket-mcp-server==0.1.3", "polymarket-mcp"]
startup_timeout_sec = 30.0
CONFIG
}

require_curl_jq() {
  check_env

  if ! command -v curl >/dev/null 2>&1; then
    echo "error: curl is required" >&2
    return 1
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "error: jq is required" >&2
    return 1
  fi
}

run_smoke() {
  require_curl_jq

  local url="https://gamma-api.polymarket.com/events?active=true&closed=false&limit=${limit}"
  local body
  body="$(curl -fsSL "$url")"

  local count
  count="$(printf '%s' "$body" | jq 'if type == "array" then length else 0 end')"
  if [[ "$count" -lt 1 ]]; then
    echo "error: public Gamma API returned no events" >&2
    return 1
  fi

  printf '%s\n' "$body" | jq '{ok: true, source: "gamma-api/events", count: length, first: .[0] | {id, slug, title, active, closed}}'
}

run_search() {
  require_curl_jq

  local body
  body="$(
    curl -fsSLG \
      --data-urlencode "q=${search_query}" \
      --data-urlencode "limit=${limit}" \
      "https://gamma-api.polymarket.com/public-search"
  )"

  printf '%s\n' "$body" | jq --arg query "$search_query" '
    def direct_markets:
      if type == "array" then .
      elif type == "object" then (.markets // .data // [])
      else []
      end;
    def events:
      if type == "object" then (.events // [])
      else []
      end;
    def event_markets:
      [events[]? | (.markets // [])[]?];
    {
      ok: true,
      source: "gamma-api/public-search",
      query: $query,
      totalResults: (
        if type == "object" then (.pagination.totalResults // ((events + direct_markets) | length))
        else (direct_markets | length)
        end
      ),
      events: events | map({
        id,
        slug,
        title,
        active,
        closed,
        volume,
        liquidity,
        endDate
      }),
      markets: (direct_markets + event_markets) | map({
        id,
        slug,
        question,
        active,
        closed,
        volume,
        liquidity,
        endDate,
        clobTokenIds
      })
    }'
}

while [[ $# -gt 0 ]]; do
  case "${1:-}" in
    --check-env)
      mode="check-env"
      shift
      ;;
    --print-codex-config)
      mode="print-codex-config"
      shift
      ;;
    --smoke)
      mode="smoke"
      shift
      ;;
    --search)
      if [[ $# -lt 2 ]]; then
        echo "error: --search requires a query" >&2
        usage >&2
        exit 2
      fi
      mode="search"
      search_query="${2:-}"
      shift 2
      ;;
    --limit)
      if [[ $# -lt 2 ]]; then
        echo "error: --limit requires a value" >&2
        usage >&2
        exit 2
      fi
      limit="${2:-}"
      if [[ ! "$limit" =~ ^[1-9][0-9]*$ ]]; then
        echo "error: --limit must be a positive integer" >&2
        exit 2
      fi
      shift 2
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

case "$mode" in
  check-env)
    check_env
    ;;
  print-codex-config)
    print_codex_config
    ;;
  smoke)
    run_smoke
    ;;
  search)
    run_search
    ;;
  "")
    usage >&2
    exit 2
    ;;
esac
