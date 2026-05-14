#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  polymarket-readonly.sh --check-env
  polymarket-readonly.sh --print-codex-config
  polymarket-readonly.sh --smoke [--limit <n>]
  polymarket-readonly.sh --search <query> [--limit <n>]
  polymarket-readonly.sh --trending [--days <n>] [--limit <n>] [--scope events|markets|both] [--format json|markdown]
  polymarket-readonly.sh --report daily|weekly [--limit <n>] [--scope events|markets|both] [--format json|markdown]
  polymarket-readonly.sh --help

Read-only Polymarket helper. It never uses private keys or authenticated trading
credentials. --smoke checks a public Gamma API endpoint only. --search uses the
Gamma public-search REST fallback with the current q= parameter. --trending uses
Gamma event/market volume rankings; the default 3-day window is ranked by the
best available Gamma proxy metric, not exact 3-day trade aggregation. --report
emits a source-grounded daily or weekly hot-topics digest.
USAGE
}

limit=""
mode=""
search_query=""
days=3
days_was_set=false
scope="events"
scope_was_set=false
format=""
format_was_set=false
report_type=""

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
  check_env || return $?

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

ranking_metric_for_days() {
  local window_days="${1:-}"
  if [[ "$window_days" -eq 1 ]]; then
    printf 'volume24hr'
  elif [[ "$window_days" -le 7 ]]; then
    printf 'volume1wk'
  else
    printf 'volume1mo'
  fi
}

ranking_mode_for_days() {
  local window_days="${1:-}"
  if [[ "$window_days" -eq 1 || "$window_days" -eq 7 ]]; then
    printf 'native'
  else
    printf 'proxy'
  fi
}

fetch_trending_scope() {
  local target_scope="${1:-}"
  local ranking_metric="${2:-}"
  local body
  body="$(
    curl -fsSLG \
      --data-urlencode "active=true" \
      --data-urlencode "closed=false" \
      --data-urlencode "limit=${limit}" \
      --data-urlencode "order=${ranking_metric}" \
      --data-urlencode "ascending=false" \
      "https://gamma-api.polymarket.com/${target_scope}"
  )"
  printf '%s\n' "$body"
}

normalize_trending_payload() {
  local body="${1:-}"
  local target_scope="${2:-}"
  local ranking_metric="${3:-}"
  local ranking_mode="${4:-}"
  local generated_at="${5:-}"
  local url_path="event"
  if [[ "$target_scope" == "markets" ]]; then
    url_path="market"
  fi
  printf '%s\n' "$body" | jq \
    --arg source "gamma-api/${target_scope}" \
    --arg scope "$target_scope" \
    --arg report "$report_type" \
    --arg urlPath "$url_path" \
    --argjson windowDays "$days" \
    --arg rankingMetric "$ranking_metric" \
    --arg rankingMode "$ranking_mode" \
    --arg generatedAt "$generated_at" '
    def items:
      if type == "array" then .
      elif type == "object" then (.data // .events // .markets // [])
      else []
      end;
    def common_fields:
      {
        id,
        slug,
        active,
        closed,
        volume,
        volume24hr,
        volume1wk,
        volume1mo,
        liquidity,
        endDate,
        url: (if (.slug // "") != "" then "https://polymarket.com/" + $urlPath + "/" + .slug else null end),
        rankingValue: (.[$rankingMetric] // null)
      };
    {
      ok: true,
      source: $source,
      scope: $scope,
      report: (if $report == "" then null else $report end),
      windowDays: $windowDays,
      rankingMetric: $rankingMetric,
      rankingMode: $rankingMode,
      generatedAt: $generatedAt,
      rankingNote: (
        if $rankingMode == "proxy" then
          "Gamma does not expose exact volume for this custom day window; results are ranked by the nearest available Gamma volume metric."
        else
          "Results are ranked by the matching Gamma volume metric for this window."
        end
      ),
      results: items | map(
        if $scope == "events" then
          common_fields + {title}
        else
          common_fields + {question, clobTokenIds}
        end
      )
    }'
}

build_trending_payload() {
  require_curl_jq || return $?

  local ranking_metric
  ranking_metric="$(ranking_metric_for_days "$days")"

  local ranking_mode
  ranking_mode="$(ranking_mode_for_days "$days")"

  local generated_at
  generated_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

  if [[ "$scope" == "both" ]]; then
    local events_body
    events_body="$(fetch_trending_scope "events" "$ranking_metric")"
    local markets_body
    markets_body="$(fetch_trending_scope "markets" "$ranking_metric")"
    local events_payload
    events_payload="$(normalize_trending_payload "$events_body" "events" "$ranking_metric" "$ranking_mode" "$generated_at")"
    local markets_payload
    markets_payload="$(normalize_trending_payload "$markets_body" "markets" "$ranking_metric" "$ranking_mode" "$generated_at")"

    jq -n \
      --arg report "$report_type" \
      --argjson windowDays "$days" \
      --arg rankingMetric "$ranking_metric" \
      --arg rankingMode "$ranking_mode" \
      --arg generatedAt "$generated_at" \
      --argjson events "$events_payload" \
      --argjson markets "$markets_payload" '
      {
        ok: true,
        source: "gamma-api",
        sources: ["gamma-api/events", "gamma-api/markets"],
        scope: "both",
        report: (if $report == "" then null else $report end),
        windowDays: $windowDays,
        rankingMetric: $rankingMetric,
        rankingMode: $rankingMode,
        generatedAt: $generatedAt,
        rankingNote: (
          if $rankingMode == "proxy" then
            "Gamma does not expose exact volume for this custom day window; results are ranked by the nearest available Gamma volume metric."
          else
            "Results are ranked by the matching Gamma volume metric for this window."
          end
        ),
        sections: {
          events: $events,
          markets: $markets
        }
      }'
  else
    local body
    body="$(fetch_trending_scope "$scope" "$ranking_metric")"
    normalize_trending_payload "$body" "$scope" "$ranking_metric" "$ranking_mode" "$generated_at"
  fi
}

render_markdown_report() {
  local payload="${1:-}"
  local title="Polymarket Trends"
  if [[ "$report_type" == "daily" ]]; then
    title="Polymarket Daily Trends"
  elif [[ "$report_type" == "weekly" ]]; then
    title="Polymarket Weekly Trends"
  fi

  printf '%s\n' "$payload" | jq -r --arg title "$title" '
    def amount:
      if . == null then "n/a"
      elif type == "number" then
        if . >= 1000000 then (((. / 1000000) * 100 | round / 100 | tostring) + "M")
        elif . >= 1000 then (((. / 1000) * 100 | round / 100 | tostring) + "K")
        else (. | tostring)
        end
      else (. | tostring)
      end;
    def item_line:
      . as $item
      | ($item.title // $item.question // $item.slug // "Untitled") as $name
      | ($item.url // "") as $url
      | "- " + (if $url != "" then "[" + $name + "](" + $url + ")" else $name end)
        + " | ranking value: " + ($item.rankingValue | amount)
        + (if ($item.volume24hr // null) != null then " | 24h: " + ($item.volume24hr | amount) else "" end)
        + (if ($item.volume1wk // null) != null then " | 1w: " + ($item.volume1wk | amount) else "" end)
        + (if ($item.liquidity // null) != null then " | liquidity: " + ($item.liquidity | amount) else "" end)
        + " | `" + ($item.slug // "no-slug") + "`";
    def section($heading; $items):
      ["## " + $heading, ""]
      + (if ($items | length) > 0 then ($items | map(item_line)) else ["No results returned."] end)
      + [""];
    def sources_text:
      if (.sources // null) then (.sources | join(", ")) else .source end;
    [
      "# " + $title,
      "",
      "- Generated: " + .generatedAt,
      "- Window: " + (.windowDays | tostring) + " day(s)",
      "- Source: " + sources_text,
      "- Ranking: " + .rankingMetric + " (" + .rankingMode + ")",
      ""
    ]
    + (
      if .scope == "both" then
        section("Hot Topics"; (.sections.events.results // []))
        + section("Hot Questions"; (.sections.markets.results // []))
      elif .scope == "events" then
        section("Hot Topics"; (.results // []))
      else
        section("Hot Questions"; (.results // []))
      end
    )
    + [
      "## Notes",
      "",
      "- " + .rankingNote,
      "- Read-only public Gamma API lookup; no credentials, signing, or trading actions used."
    ]
    | .[]'
}

emit_trending() {
  local payload
  payload="$(build_trending_payload)"
  if [[ "$format" == "markdown" ]]; then
    render_markdown_report "$payload"
  else
    printf '%s\n' "$payload"
  fi
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
    --trending)
      mode="trending"
      shift
      ;;
    --report)
      if [[ $# -lt 2 ]]; then
        echo "error: --report requires daily or weekly" >&2
        usage >&2
        exit 2
      fi
      mode="report"
      report_type="${2:-}"
      if [[ "$report_type" != "daily" && "$report_type" != "weekly" ]]; then
        echo "error: --report must be daily or weekly" >&2
        exit 2
      fi
      shift 2
      ;;
    --days)
      if [[ $# -lt 2 ]]; then
        echo "error: --days requires a value" >&2
        usage >&2
        exit 2
      fi
      days="${2:-}"
      if [[ ! "$days" =~ ^[1-9][0-9]*$ ]]; then
        echo "error: --days must be a positive integer" >&2
        exit 2
      fi
      if [[ "$days" -gt 31 ]]; then
        echo "error: --days must be 31 or less for fast Gamma trending" >&2
        exit 2
      fi
      days_was_set=true
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
    --scope)
      if [[ $# -lt 2 ]]; then
        echo "error: --scope requires a value" >&2
        usage >&2
        exit 2
      fi
      scope="${2:-}"
      if [[ "$scope" != "events" && "$scope" != "markets" && "$scope" != "both" ]]; then
        echo "error: --scope must be events, markets, or both" >&2
        exit 2
      fi
      scope_was_set=true
      shift 2
      ;;
    --format)
      if [[ $# -lt 2 ]]; then
        echo "error: --format requires a value" >&2
        usage >&2
        exit 2
      fi
      format="${2:-}"
      if [[ "$format" != "json" && "$format" != "markdown" ]]; then
        echo "error: --format must be json or markdown" >&2
        exit 2
      fi
      format_was_set=true
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

if [[ "$mode" == "report" ]]; then
  if [[ "$days_was_set" == "false" ]]; then
    if [[ "$report_type" == "daily" ]]; then
      days=1
    else
      days=7
    fi
  fi
  if [[ "$scope_was_set" == "false" ]]; then
    scope="both"
  fi
fi

if [[ "$format_was_set" == "false" ]]; then
  if [[ "$mode" == "report" ]]; then
    format="markdown"
  else
    format="json"
  fi
fi

if [[ -z "$limit" ]]; then
  if [[ "$mode" == "trending" || "$mode" == "report" ]]; then
    limit=10
  else
    limit=1
  fi
fi

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
  trending)
    emit_trending
    ;;
  report)
    emit_trending
    ;;
  "")
    usage >&2
    exit 2
    ;;
esac
