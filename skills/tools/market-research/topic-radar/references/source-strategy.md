# Topic Radar Source Strategy

## Purpose

`topic-radar` is a read-only AI/technology trend aggregator and lower-level
data engine. It is meant to answer "what source signals exist for this topic?"
rather than provide the final personalized daily brief, a complete archive, or a
definitive news feed.

## Source Roles

- `official`: source-of-record release and policy changes from AI labs and
  platform vendors.
- `hn`: developer discussion and early community reaction.
- `github`: open-source momentum, tool launches, and implementation evidence.
- `arxiv`: research flow for AI, ML, and language-model work.
- `hf`: model, dataset, and demo ecosystem activity.
- `polymarket`: market attention and uncertainty around public events.
- `news`: broader mainstream coverage via public news search.

## Profiles

- `terry-ai-tech` is the default personal profile. It tracks AI agents,
  agentic coding, model releases, developer tools, AI infrastructure, inference
  serving, semiconductors, NVIDIA, robotics, embodied AI, OpenAI, Anthropic,
  Google DeepMind, and Hugging Face.
- `ai-tech` is the generic baseline profile retained for broader AI and
  technology scans.

## Presets

- `radar` is the broad source scan. It uses the default personal profile and
  all source roles.
- `ai-news` is the fast daily news entrypoint. It narrows sources to
  `official,news,hn`, uses a five-day window, enables clustered brief output,
  keeps a short public-response cache for follow-up questions, and uses Google
  News RSS by default to avoid routine GDELT rate-limit stalls.
- Agents may use personal memory before invoking the script to choose topics,
  source filters, or whether to refresh cached source responses. Memory is only
  a steering input; output claims must remain grounded in returned source items.

## Relationship to Daily Brief

- `daily-brief` should be the default user-facing workflow for daily information
  intake. It resolves the user's intent, applies stable preference steering,
  calls `topic-radar --format json`, and writes the final concise brief.
- `topic-radar` should stay responsible for source acquisition, source fallback,
  cache, ranking, and machine-readable report structure.
- Do not duplicate fetchers, source scoring, cache policy, RSS/API parsing, or
  Polymarket fallback logic in `daily-brief`.

## Ranking Model

The first implementation uses a transparent heuristic:

- source weight
- engagement proxy from the source, when available
- recency within the requested window
- topic keyword match
- cross-source duplication bonus

Do not present the score as objective importance. It is a triage score for
morning review and agent handoff.

## Expansion Rules

- Prefer public, read-only APIs or RSS/Atom feeds before browser scraping.
- Prefer read-only Polymarket MCP output over direct REST when the current
  agent runtime exposes the `polymarket` MCP tools. Pass exported MCP results
  through `--polymarket-mcp-json`, then let the script fall back to the
  read-only helper when MCP output is unavailable.
- Keep source-specific failures isolated in `errors`.
- Run independent public source fetches in parallel when possible; keep source
  failures isolated so one slow upstream does not block the whole digest.
- Use the public-response cache only for short-lived acceleration. Bypass it
  with `--refresh` when the user asks for exact latest/current evidence.
- For `news`, the broad `radar` preset tries GDELT first and falls back to
  Google News RSS when GDELT is unavailable, malformed, or empty. The fast
  `ai-news` preset uses Google News RSS directly.
- Add source metadata to every item so reports remain auditable.
- Use JSON output for automation and Markdown output for human daily review.
- Do not add posting, trading, paid-account, or credentialed actions to this skill.
