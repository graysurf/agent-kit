---
name: polymarket-readonly
description: Use when researching Polymarket markets, events, prices, order books, public wallet analytics, or the read-only Polymarket MCP setup without trading credentials.
---

# Polymarket Readonly

## Contract

Prereqs:

- Network access.
- Preferred local MCP server: `polymarket`, backed by `uvx --from polymarket-mcp-server==0.1.3 polymarket-mcp`.
- `curl` and `jq` available for public REST fallback checks.

Inputs:

- Natural-language market/event/topic questions.
- Polymarket market slugs, event slugs, token IDs, condition IDs, tag names, or public wallet addresses.
- Optional request to inspect or smoke-test the local read-only MCP setup.

Outputs:

- Market/event summaries, public price/orderbook context, or public wallet analytics.
- Recent trending/hot-topic rankings with explicit source, window, metric, and proxy metadata.
- Daily or weekly Markdown digests for quick trend review.
- Source-grounded notes that separate observed Polymarket data from inference.
- MCP setup or smoke-test diagnostics when requested.
- REST fallback search output when MCP free-text search is unavailable or known-broken.

Exit codes:

- `0`: success
- `1`: failure
- `2`: usage error
- `3`: unsafe Polymarket trading credential environment detected

Failure modes:

- If the user asks to place, cancel, fund, bridge, redeem, approve, sign, or automate trades,
  refuse that action and offer a read-only market research alternative.
- If any Polymarket private key or authenticated trading credential is present in the environment, stop before launching MCP or API checks.
- If the MCP server is unavailable, fall back to Polymarket public REST endpoints rather than requesting credentials.

## Scripts (only entrypoints)

- `$AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh`

## References

- Read [references/mcp-options.md](references/mcp-options.md) when choosing or refreshing the MCP implementation.
- Read [references/public-api.md](references/public-api.md) when using REST fallbacks or explaining auth boundaries.

## Workflow

1. Treat this skill as read-only research tooling. Never request, configure, or use wallet private
   keys, seed phrases, CLOB API credentials, builder credentials, approvals, order placement, or
   order cancellation.
2. Prefer the local `polymarket` MCP server when available. It should use `polymarket-mcp-server` in read-only mode with no env block.
3. For quick health checks, run:

   ```bash
   $AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh --smoke
   ```

4. For free-text market discovery, be aware that `polymarket-mcp-server==0.1.3`
   sends `query=` to Gamma `/public-search`, while the public API currently
   expects `q=`. That upstream mismatch returns HTTP 422 and is masked by the
   MCP server as a generic tool error. Until a newer MCP package fixes this,
   use the REST fallback:

   ```bash
   $AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh --search "fed decision" --limit 5
   ```

5. For recent popular topics, use the repeatable trending workflow:

   ```bash
   $AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh --trending --days 3 --limit 10
   ```

   The default is a recent 3-day event ranking. Gamma currently exposes
   `volume24hr`, `volume1wk`, and `volume1mo`, but not exact `volume3d`.
   This helper maps `--days 1` to `volume24hr` with `rankingMode: "native"`;
   `--days 7` to `volume1wk` with `rankingMode: "native"`; `--days 2..6`
   to `volume1wk` with `rankingMode: "proxy"`; and
   `--days 8..31` to `volume1mo` with `rankingMode: "proxy"`. Do not present
   proxy output as exact custom-window volume. Use `--scope markets` when the
   user wants market/question-level results instead of event/topic-level results,
   or `--scope both` when they want both topic-level and question-level results.
6. For daily or weekly trend review, prefer the report workflow:

   ```bash
   $AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh --report daily
   $AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh --report weekly
   ```

   Reports default to Markdown, `--scope both`, and `--limit 10`. Daily reports
   default to `--days 1` and weekly reports default to `--days 7`. Use
   `--format json` when another tool needs a structured report payload.
7. For market discovery without MCP, use public Gamma endpoints. For live price/orderbook context,
   use public CLOB read endpoints. For wallet analytics, use public Data API endpoints and state
   that wallet data is public/onchain-derived.
8. Cite the concrete tool result, local config, or official API doc when the answer depends on auth, setup, or current market data.
9. Keep analysis non-advisory unless the user explicitly asks for a forecast. Do not frame output as financial, betting, or trading advice.
