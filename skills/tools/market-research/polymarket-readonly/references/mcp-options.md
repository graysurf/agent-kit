# Polymarket MCP Options

Use this reference when choosing, validating, or changing the MCP server for read-only Polymarket research.

## Preferred

`polymarket-mcp-server`

- Package: `polymarket-mcp-server`
- Entrypoint: `uvx --from polymarket-mcp-server==0.1.3 polymarket-mcp`
- Scope: Gamma discovery, Data API wallet/activity reads, public CLOB prices/orderbooks/history.
- Safety model: intentionally read-only in the `0.1.x` line; it does not place trades, sign orders, manage keys, or require wallet credentials.
- Local Codex config should use no `env` block for this server.

## Acceptable Fallbacks

`@igoforth/polymarket-mcp`

- Use only when a Node/npx fallback is needed.
- Scope is broad public Gamma, CLOB, and Data API tooling.
- README states that tools use public Polymarket endpoints and need no API keys.

`@iqai/mcp-polymarket`

- Use only in read-only mode with no `POLYMARKET_PRIVATE_KEY`.
- Its source registers trading tools when a private key is configured, so do not make it the default for this skill.

## Avoid By Default

- Trading/copy-trading MCPs such as `polymarket-agent-mcp` or `@carbon-copy/polymarket-mcp`.
- Any MCP that requires `POLYMARKET_PRIVATE_KEY`, `POLYMARKET_API_SECRET`, order signing, approvals, or live trading mode.
- `graph-polymarket-mcp` unless the user specifically wants The Graph analytics and accepts a separate `GRAPH_API_KEY`.

## Refresh Checklist

- Confirm current package metadata before changing the recommended install command.
- Confirm the tool surface does not expose order placement, cancellation, approvals, signing, bridging, or redemption.
- Keep Polymarket credentials out of tracked files and out of Codex MCP config for this skill.
