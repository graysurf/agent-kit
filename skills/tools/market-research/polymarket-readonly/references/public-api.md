# Polymarket Public API Notes

Use this reference when answering auth-boundary questions or falling back from MCP to direct public REST calls.

## Public Surfaces

- Gamma API: `https://gamma-api.polymarket.com`
  - Market and event discovery, tags, series, comments, sports, search, and public profiles.
- Data API: `https://data-api.polymarket.com`
  - Public positions, trades, activity, holder data, open interest, leaderboards, and analytics.
- CLOB public reads: `https://clob.polymarket.com`
  - Prices, order books, midpoints, spreads, and price history.

These public surfaces do not need Polymarket login, API key, wallet private key, or signing.

## Authenticated Surfaces

Authenticated CLOB and trading workflows are outside this skill. Do not handle:

- placing or cancelling orders
- open order management for an authenticated account
- approvals, allowance updates, bridging, redeeming, or withdrawals
- L1 wallet signing or L2 API credential generation
- private keys, seed phrases, or API secrets

## Fallback Examples

Market/event health check:

```bash
curl -fsSL 'https://gamma-api.polymarket.com/events?active=true&closed=false&limit=1'
```

Market search:

```bash
curl -fsSL 'https://gamma-api.polymarket.com/public-search?q=ai&limit=5'
```

Skill fallback search:

```bash
$AGENT_HOME/skills/tools/market-research/polymarket-readonly/scripts/polymarket-readonly.sh --search ai --limit 5
```

Do not use `query=` for `/public-search`; the current Gamma API expects `q=`.

When reporting results, state which endpoint or MCP tool produced the data and avoid unsupported conclusions.
