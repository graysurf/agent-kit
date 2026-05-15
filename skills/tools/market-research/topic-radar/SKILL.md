---
name: topic-radar
description:
  Aggregate read-only AI and technology trend signals from Polymarket, Hacker News, GitHub, arXiv, Hugging Face, official
  sources, and news search into source-grounded Markdown or JSON digests. Use directly for source-level radar scans,
  machine-consumable output, source tuning, or as the lower-level data engine for daily-brief.
---

# Topic Radar

## Contract

Prereqs:

- Network access for live lookups.
- `uv` available from the agent-kit repository environment.
- Optional upstreams may rate-limit anonymous requests; the skill must degrade per-source instead of failing the whole digest.
- Polymarket source support prefers read-only MCP tool output when available; otherwise it falls back to the
  `$AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh` helper.

Inputs:

- Natural-language AI or technology topics.
- Optional profile name: `terry-ai-tech` by default, `ai-tech` for the generic baseline, or aliases `terry`, `personal`, and `default`.
- Optional preset: `radar` by default, or `ai-news` for a faster daily AI news scan focused on official/news/HN sources.
- Optional source list: `polymarket`, `hn`, `github`, `arxiv`, `hf`, `official`, `news`, or `all`.
- Daily, weekly, or monthly report request, custom rolling day window, fixed `--from/--to` or `--month` window, result limit, parallel fetch
  count, cache TTL, news provider strategy, brief mode, and output format.
- Optional Polymarket MCP JSON export path passed with `--polymarket-mcp-json`.

Outputs:

- Source-grounded AI/technology trend digest in Markdown or JSON.
- Optional clustered brief for fast reading across product, agent/tooling, enterprise, security/governance, and research/open-ecosystem signals.
- Ranked cross-source signal list with source metadata, URLs, timestamps, fixed or rolling window metadata, score rationale, and per-source
  sections.
- Per-source errors when an upstream is unavailable, rate-limited, or malformed, including short response snippets when available.
- Public-response cache metadata so repeated follow-up scans are auditable.
- Sample-mode output for offline smoke checks and report-format review.

Exit codes:

- `0`: success
- `1`: failure
- `2`: usage error
- `3`: unsafe delegated source environment detected

Failure modes:

- Unknown source, report type, format, profile, invalid fixed-window shape, or invalid numeric option.
- Live source returns invalid data, times out, or rate-limits; the affected source is reported in `errors`, while other sources continue.
- The broad `radar` preset uses `news-provider=auto`: GDELT first, then Google News RSS fallback when GDELT is unavailable or empty.
- The faster `ai-news` preset uses `news-provider=google` by default to avoid GDELT rate-limit stalls during daily scans.
- Polymarket MCP output is missing, malformed, or has no usable records; continue to helper fallback unless `--polymarket-fallback none` is
  set.
- Delegated Polymarket helper detects unsafe trading credentials; stop with exit `3`.

## Scripts (only entrypoints)

- `$AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh`

## References

- Read [references/source-strategy.md](references/source-strategy.md) before changing source selection, ranking, or report sections.

## Role Boundary

- Use `topic-radar` directly when the user asks for source-level scanning, custom sources, raw Markdown/JSON digest output, or automation
  input.
- Use `daily-brief` when the user wants the normal daily information entrypoint: concise user-language synthesis, preference steering,
  freshness notes, and source-health explanation.
- `topic-radar` owns source fetching, ranking, fallback behavior, public-response caching, brief clusters, and per-source errors.
- `daily-brief` must not reimplement fetchers, ranking, cache, RSS/API parsing, or Polymarket fallback logic; it should consume
  `topic-radar --format json`.

## Workflow

1. Treat this skill as read-only content and trend research. Do not request or configure trading credentials, social posting credentials, or
   paid news API keys by default.

2. For "AI news today / this week / these days" requests, start with the faster AI news preset. It uses a 5-day window, clustered brief
   output, public-response caching, Google News RSS for mainstream coverage, and the source order `official,news,hn`:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset ai-news
   ```

   Use `--refresh` when the user asks for exact latest/current results and cached responses should be bypassed:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset ai-news --refresh
   ```

3. Use the broad radar preset when the user asks for general AI/Tech trend scanning across market, developer, research, model, official, and
   news surfaces. The default profile tracks AI agents, agentic coding, model releases, developer tools, AI infrastructure, inference
   serving, semiconductors, NVIDIA, robotics, embodied AI, OpenAI, Anthropic, Google DeepMind, and Hugging Face:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --report daily
   ```

4. Use personal memory only as a steering layer for recurring interests and source preferences before running the script. Do not write
   secrets, temporary task state, or project state into memory. Keep the report grounded in the script output and linked source items.

5. When Polymarket is requested and the current agent has the `polymarket` MCP tools, query read-only MCP first:

   - `gamma_list_events` with `active=true`, `closed=false`, and a small `limit`
   - `gamma_list_markets` with `active=true`, `closed=false`, and a small `limit`
   - `gamma_search_public` for the user's focused topic when broad lists are too noisy

   Save those raw MCP results as JSON shaped like this:

   ```json
   {
     "events": [],
     "markets": [],
     "search": []
   }
   ```

   Then pass the file to the radar:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh \
     --sources polymarket,hn,github \
     --polymarket-mcp-json /path/to/polymarket-mcp.json \
     --report daily
   ```

6. If no MCP output is available, omit `--polymarket-mcp-json`; the script falls back to the read-only `polymarket-readonly` helper and
   reports per-source errors if the local network blocks Polymarket REST.

7. For focused research, pass topics and source filters:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh \
     --topic "AI agents" \
     --topic "developer tools" \
     --sources hn,github,arxiv,hf,polymarket \
     --report weekly
   ```

8. For monthly trend archive work, use a fixed calendar window rather than a rolling `--days` window:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh \
     --preset radar \
     --report monthly \
     --month 2026-01 \
     --format json
   ```

   For a partial current month, use explicit inclusive dates:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh \
     --preset radar \
     --from 2026-05-01 \
     --to 2026-05-15 \
     --format json
   ```

   Treat fixed windows as source-bounded evidence. Some sources are current snapshots rather than reliable historical archives; the JSON
   `errors` field reports those gaps instead of silently inventing monthly history.

9. Use JSON when another tool, scheduled job, or agent synthesis step will consume the output:

   ```bash
   $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset ai-news --format json
   ```

10. Use sample mode for smoke checks, demos, or local validation without network access:

    ```bash
    $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --sample --format markdown
    ```

11. Keep the report source-grounded. Separate observed source signals from inference, and do not present heuristic ranking as objective
    importance.
