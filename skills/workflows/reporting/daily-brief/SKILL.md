---
name: daily-brief
description:
  Prepare a source-grounded daily information brief for recurring AI/technology or user-selected topics. Use as the default
  daily entrypoint when the user asks for today's news, this week's signals, a morning brief, "what should I know", or a
  personalized synthesis; orchestrates topic-radar JSON output with stable preferences and does not implement its own source
  fetchers.
---

# Daily Brief

## Contract

Prereqs:

- The topic-radar script is available for source acquisition, ranking, cache, and JSON output:
  `$AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh`.
- Network access is available for live source lookups unless the user explicitly accepts offline/sample output.
- Home-scope external-lookup policy has been satisfied when live sources are queried.
- Personal memory, when available, is used only for stable topic/source preferences and never as evidence for news claims.

Inputs:

- Natural-language brief request, such as "AI news this week", "what should I watch today", "morning brief", or a focused topic.
- Optional topic list, timeframe, source preference, freshness requirement, audience, and depth.
- Optional monthly trend-backfill request for a fixed historical month or year-to-date set of months.
- Optional instruction to force latest/live results, which maps to topic-radar `--refresh`.
- Stable preferences from memory, such as recurring AI/Tech interests or preferred report style.
- Optional request to keep local history, plus an explicit record folder when the user wants durable tracking.

Outputs:

- Concise brief in the user's language with source links for material claims.
- Topline items, topic sections, and optional follow-up angles for deeper reading.
- Freshness and source-health note covering `generatedAt`, `windowDays`, cache state, refresh mode, and source errors from topic-radar JSON.
- Explicit separation between observed source signals and agent inference.
- Optional history records under the user-selected record folder.
- Optional monthly trend records with fixed-window metadata when the user asks for durable archive backfill.

Exit codes:

- N/A (instruction-first workflow; no standalone entrypoint)

Failure modes:

- `topic-radar` is unavailable, fails, or returns malformed JSON; report the command failure and do not invent a brief.
- Live sources are unavailable or rate-limited; include source gaps from topic-radar and synthesize only from returned items.
- Returned items are too thin for the requested topic/window; say so and offer a narrower or broader follow-up query.
- Memory is unavailable or irrelevant; continue from the user's request without treating that as a blocker.
- Durable history was requested but no record folder is known; ask the user to choose a folder before writing records.
- Record folder writes fail; report the path and failure, but still provide the brief if source synthesis succeeded.

## Entrypoint

- None. This is an instruction-first workflow skill. Execute it by invoking topic-radar and synthesizing its JSON output.

## Skill Roles

- `daily-brief` is the user-facing daily entrypoint. It owns intent resolution, preference steering, source-health explanation, and concise
  synthesis in the user's language.
- `topic-radar` is the lower-level radar engine. It owns source fetching, source fallback behavior, cache, ranking, clustered JSON/Markdown
  output, and source-specific errors.
- `polymarket-readonly` is the market-only helper behind topic-radar's Polymarket source. Use it directly only when the user specifically asks
  for Polymarket markets, odds, order books, or wallet/public market details.

Do not split source fetchers, ranking, cache, RSS/API parsing, or Polymarket fallback logic into `daily-brief`. If those behaviors need to
change, update `topic-radar`.

## Workflow

1. Resolve the brief intent.
   - Default underspecified daily information requests to AI/Tech unless the user names another topic.
   - Use the user's explicit timeframe when given. For "today", "this week", or "these days", state the absolute date/window in the reply.
   - Ask only if the topic or audience is ambiguous enough that a reasonable default would produce the wrong brief.

2. Apply stable preference steering.
   - Use memory only for recurring interests, source preferences, and output style.
   - Do not cite memory as news evidence.
   - Do not write or update memory unless the user explicitly asks for that.

3. Choose the topic-radar query.
   - Default daily AI/Tech brief:

     ```bash
     $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset ai-news --format json
     ```

   - Exact latest/current request:

     ```bash
     $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset ai-news --format json --refresh
     ```

   - Focused topic:

     ```bash
     $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset ai-news --format json --topic "<topic>"
     ```

   - Broad scan across research, open source, markets, and model ecosystem:

     ```bash
     $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset radar --format json
     ```

   - Monthly trend archive:

     ```bash
     $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset radar --report monthly --month 2026-01 --format json
     ```

   - Partial current-month trend archive:

     ```bash
     $AGENT_HOME/skills/tools/market-research/topic-radar/scripts/topic-radar.sh --preset radar --from 2026-05-01 --to 2026-05-15 --format json
     ```

4. Parse the JSON output.
   - Prefer `brief.clusters` for the first synthesis pass when present.
   - Use `items` and `sections` to add source links and avoid unsupported claims.
   - Carry through `errors` and `cache` metadata instead of hiding source failures.

5. Write the daily brief.
   - Lead with 3-5 high-signal bullets.
   - Use compact sections such as `Models/Products`, `Agents/Developer Tools`, `Enterprise Adoption`, `Safety/Governance`, and
     `Research/Open Source`, adapted to the brief language.
   - Keep each material claim source-linked.
   - Mark inference explicitly when connecting multiple source signals.
   - Include a short freshness/source-status note with the absolute date/window, cache/refresh state, and source gaps.

6. Write monthly trend records when requested.
   - Use `topic-radar` fixed-window JSON, not rolling `--days`, for historical month records.
   - For year-to-date backfill, create one record per month. Treat the current month as partial through the current absolute date unless the
     user gives a different end date.
   - Lead each monthly record with 3-6 source-grounded trends, then sections for product/model releases, agents/developer tools,
     infrastructure, research/open source, market/community signals, and source gaps as applicable.
   - Mark inference explicitly when describing trend movement across several source items.
   - Do not cite older local records as evidence for the month; cite the source links returned for that fixed window.
   - Use `trends/YYYY/YYYY-MM-<topic-slug>.md` for rendered monthly trend records and `raw/monthly/YYYY/YYYY-MM-<topic-slug>.json` for the
     source JSON when the selected record folder supports this layout.
   - Append `index.jsonl` entries with `recordType: "monthly-trend"`, `periodStart`, `periodEnd`, `completePeriod`, `briefPath`,
     `rawPath`, `sourceCount`, `sources`, `tags`, and source `errors` when available.

7. Write history records only when requested.
   - Do not hardcode a record location. Use the user's provided folder, an existing project record folder the user points to, or ask the user
     to choose one before writing durable records.
   - Do not initialize git, create remotes, or push the record folder unless the user explicitly asks for repository setup.
   - Use date-first storage with topic/query metadata:

     ```text
     <record-folder>/
     ├── README.md
     ├── index.jsonl
     ├── briefs/YYYY/MM/YYYY-MM-DD-<slug>.md
     ├── raw/YYYY/MM/YYYY-MM-DD-<slug>.json
     └── topics/<topic-slug>.md
     ```

   - Create `README.md` when absent to document the local schema and source-citation expectations.
   - Write the rendered brief to `briefs/YYYY/MM/YYYY-MM-DD-<slug>.md`.
   - Append one JSON object to `index.jsonl` with relative paths plus `generatedAt`, `date`, `topic`, `query`, `window`, `language`,
     `sourceCount`, `sources`, `tags`, and `errors` when available.
   - Store the topic-radar JSON under `raw/` when available and useful for future trend tracking; skip it if the user wants markdown-only
     records.
   - Update `topics/<topic-slug>.md` only for explicit tracking requests or when the user asks for a topic timeline. Keep these notes concise
     and source-linked.

## Output Style

- Match the user's language. Preserve precise English names for models, companies, APIs, repositories, and standards.
- Keep the brief skimmable. Prefer source-grounded bullets over long narrative.
- Do not present heuristic ranking as objective importance.
- Do not make trading, investment, product, or legal recommendations from the brief alone.

## Direct Usage Timing

- Use `daily-brief` when the user wants a readable daily information entrypoint, personalized synthesis, or "what matters now" answer.
- Use `topic-radar` directly when the user wants raw source sections, JSON/Markdown radar output, source tuning, or a machine-consumable digest.
- Use `polymarket-readonly` directly when the question is specifically about Polymarket markets, prices, public odds, or read-only wallet/activity
  research.
