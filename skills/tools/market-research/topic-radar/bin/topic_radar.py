#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

VERSION = "0.3.0"

PROFILE_TOPICS = {
    "ai-tech": [
        "AI agents",
        "OpenAI",
        "Anthropic",
        "LLM",
        "developer tools",
        "model releases",
        "NVIDIA",
        "Hugging Face",
    ],
    "terry-ai-tech": [
        "AI agents",
        "agentic coding",
        "model releases",
        "developer tools",
        "AI infrastructure",
        "inference serving",
        "semiconductors",
        "NVIDIA",
        "robotics",
        "embodied AI",
        "OpenAI",
        "Anthropic",
        "Google DeepMind",
        "Hugging Face",
    ],
}
PROFILE_ALIASES = {
    "default": "terry-ai-tech",
    "personal": "terry-ai-tech",
    "terry": "terry-ai-tech",
}
DEFAULT_PROFILE = "terry-ai-tech"
DEFAULT_TOPICS = PROFILE_TOPICS[DEFAULT_PROFILE]
DEFAULT_SOURCES = ["polymarket", "hn", "github", "arxiv", "hf", "official", "news"]
AI_NEWS_TOPICS = [
    "AI",
    "AI agents",
    "model releases",
    "developer tools",
    "AI infrastructure",
    "OpenAI",
    "Anthropic",
    "Google DeepMind",
]
SOURCE_ALIASES = {
    "all": "all",
    "polymarket": "polymarket",
    "hn": "hn",
    "hackernews": "hn",
    "hacker-news": "hn",
    "github": "github",
    "arxiv": "arxiv",
    "hf": "hf",
    "huggingface": "hf",
    "hugging-face": "hf",
    "official": "official",
    "rss": "official",
    "news": "news",
    "gdelt": "news",
}
SOURCE_LABELS = {
    "polymarket": "Market Attention",
    "hn": "Developer Discussion",
    "github": "Open Source Momentum",
    "arxiv": "Research",
    "hf": "Model Ecosystem",
    "official": "Official Releases",
    "news": "Mainstream Coverage",
}
SOURCE_WEIGHTS = {
    "official": 30.0,
    "hn": 25.0,
    "github": 22.0,
    "arxiv": 20.0,
    "hf": 18.0,
    "polymarket": 15.0,
    "news": 12.0,
}
USER_AGENT = "agent-kit-topic-radar/0.3 (+https://github.com/sympoies/agent-kit)"
POLYMARKET_MCP_SOURCE_DETAIL = "polymarket-mcp"

OFFICIAL_FEEDS = [
    ("OpenAI News", "https://openai.com/news/rss.xml"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    ("NVIDIA Blog", "https://blogs.nvidia.com/feed/"),
    ("Microsoft AI Blog", "https://blogs.microsoft.com/ai/feed/"),
    ("Meta Newsroom", "https://about.fb.com/news/feed/"),
]
OFFICIAL_HTML_PAGES = [
    ("Anthropic News", "https://www.anthropic.com/news", "https://www.anthropic.com"),
]
OFFICIAL_PAGE_CATEGORIES = (
    "Announcements",
    "Company",
    "Engineering",
    "Policy",
    "Product",
    "Research",
)
PRESETS = {
    "radar": {
        "topics": None,
        "sources": DEFAULT_SOURCES,
        "days": None,
        "limit": 10,
        "timeout": 15,
        "brief": False,
        "cache_ttl_minutes": 15,
        "news_provider": "auto",
    },
    "ai-news": {
        "topics": AI_NEWS_TOPICS,
        "sources": ["official", "news", "hn"],
        "days": 5,
        "limit": 8,
        "timeout": 8,
        "brief": True,
        "cache_ttl_minutes": 20,
        "news_provider": "google",
    },
}
PRESET_ALIASES = {
    "default": "radar",
    "daily": "ai-news",
    "news": "ai-news",
    "ai": "ai-news",
    "ai_news": "ai-news",
}
BRIEF_CLUSTERS = [
    (
        "Model And Product Releases",
        (
            "model",
            "release",
            "gpt",
            "claude",
            "gemini",
            "deepseek",
            "qwen",
            "hugging face",
            "chatgpt",
            "codex",
        ),
    ),
    (
        "Agents And Developer Tools",
        (
            "agent",
            "agentic",
            "coding",
            "developer",
            "codex",
            "claude code",
            "cursor",
            "mcp",
            "workflow",
            "automation",
            "orchestration",
        ),
    ),
    (
        "Enterprise Adoption",
        (
            "enterprise",
            "business",
            "finance",
            "erp",
            "sap",
            "uipath",
            "microsoft",
            "notion",
            "customer",
            "adoption",
            "rollout",
        ),
    ),
    (
        "Security Safety And Governance",
        (
            "security",
            "safety",
            "governance",
            "sandbox",
            "supply chain",
            "attack",
            "risk",
            "policy",
            "privacy",
            "credential",
            "firewall",
        ),
    ),
    (
        "Research And Open Ecosystem",
        (
            "research",
            "paper",
            "arxiv",
            "benchmark",
            "open source",
            "github",
            "dataset",
            "leaderboard",
            "huggingface",
            "hugging face",
        ),
    ),
]
OTHER_BRIEF_CLUSTER = "Other Signals"


class UsageError(ValueError):
    pass


class LinkTextParser(HTMLParser):
    def __init__(self, href_prefix: str) -> None:
        super().__init__(convert_charrefs=True)
        self.href_prefix = href_prefix
        self._active_href: str | None = None
        self._active_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href and href.startswith(self.href_prefix):
            self._active_href = href
            self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_href:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._active_href:
            return
        self.links.append((self._active_href, normalize_space(" ".join(self._active_text))))
        self._active_href = None
        self._active_text = []


class TextOnlyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


@dataclass
class RadarItem:
    source: str
    title: str
    url: str
    published_at: str | None = None
    summary: str | None = None
    engagement: float = 0.0
    score: float = 0.0
    reason: str = ""
    source_detail: str | None = None
    tags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    also_seen_in: list[str] = field(default_factory=list)
    cross_source_count: int = 1

    def to_json(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "sourceLabel": SOURCE_LABELS.get(self.source, self.source),
            "sourceDetail": self.source_detail,
            "title": self.title,
            "url": self.url,
            "publishedAt": self.published_at,
            "summary": self.summary,
            "engagement": self.engagement,
            "score": round(self.score, 4),
            "reason": self.reason,
            "tags": self.tags,
            "alsoSeenIn": self.also_seen_in,
            "crossSourceCount": self.cross_source_count,
            "raw": self.raw,
        }


def now_utc() -> datetime:
    return datetime.now(UTC)


def iso_now() -> str:
    return now_utc().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        return datetime.fromisoformat(text).astimezone(UTC)
    except ValueError:
        try:
            return parsedate_to_datetime(value).astimezone(UTC)
        except (TypeError, ValueError, AttributeError):
            return None


def parse_compact_gdelt_datetime(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    return value


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_html_text(value: str | None) -> str:
    text = value or ""
    if "<" not in text and "&" not in text:
        return normalize_space(text)
    parser = TextOnlyParser()
    try:
        parser.feed(text)
    except Exception:  # noqa: BLE001 - best-effort cleanup for malformed feed HTML.
        return normalize_space(re.sub(r"<[^>]+>", " ", text))
    return normalize_space(" ".join(parser.parts))


def topic_terms(topics: list[str]) -> list[str]:
    terms: list[str] = []
    for topic in topics:
        cleaned = normalize_space(topic).lower()
        if cleaned:
            terms.append(cleaned)
            terms.extend(part for part in re.split(r"[^a-z0-9.+#-]+", cleaned) if len(part) >= 4)
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            unique.append(term)
    return unique


def interest_match_score(item: RadarItem, topics: list[str]) -> float:
    haystack = " ".join([item.title, item.summary or "", " ".join(item.tags)]).lower()
    if not haystack:
        return 0.0
    score = 0.0
    for term in topic_terms(topics):
        if topic_term_matches(haystack, term):
            score += 1.0 if " " in term else 0.4
    return min(score, 6.0)


def topic_term_matches(haystack: str, term: str) -> bool:
    if " " in term:
        return term in haystack
    if term == "ai":
        return re.search(r"(?<![a-z0-9])a\.?i\.?(?![a-z0-9])", haystack) is not None
    if len(term) <= 3:
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", haystack) is not None
    return term in haystack


def recency_score(published_at: str | None, days: int) -> float:
    published = parse_iso_datetime(published_at)
    if published is None:
        return 0.0
    age_hours = max(0.0, (now_utc() - published).total_seconds() / 3600.0)
    window_hours = max(float(days * 24), 1.0)
    return max(0.0, 8.0 * (1.0 - min(age_hours / window_hours, 1.0)))


def compute_score(item: RadarItem, topics: list[str], days: int) -> RadarItem:
    base = SOURCE_WEIGHTS.get(item.source, 10.0)
    engagement = math.log1p(max(item.engagement, 0.0)) * 2.0
    interest = interest_match_score(item, topics) * 6.0
    item.score = base + engagement + interest + recency_score(item.published_at, days)
    return item


def canonical_key(item: RadarItem) -> str:
    if item.url:
        parsed = urllib.parse.urlsplit(item.url)
        netloc = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.rstrip("/")
        return f"url:{netloc}{path}"
    title = re.sub(r"[^a-z0-9]+", " ", item.title.lower()).strip()
    return f"title:{title[:120]}"


def dedupe_and_rank(items: list[RadarItem], topics: list[str], days: int) -> list[RadarItem]:
    merged: dict[str, RadarItem] = {}
    seen_sources: dict[str, set[str]] = {}
    for item in items:
        compute_score(item, topics, days)
        key = canonical_key(item)
        if key not in merged:
            merged[key] = item
            seen_sources[key] = {item.source}
            continue
        existing = merged[key]
        seen_sources[key].add(item.source)
        existing.score = max(existing.score, item.score)
        existing.engagement += item.engagement
        if item.source not in existing.also_seen_in and item.source != existing.source:
            existing.also_seen_in.append(item.source)
        if not existing.summary and item.summary:
            existing.summary = item.summary
        if not existing.published_at and item.published_at:
            existing.published_at = item.published_at
    for key, item in merged.items():
        item.cross_source_count = len(seen_sources[key])
        if item.cross_source_count > 1:
            item.score += 10.0 * (item.cross_source_count - 1)
            item.reason = f"{item.reason}; seen across {item.cross_source_count} sources"
    return sorted(merged.values(), key=lambda x: x.score, reverse=True)


def http_get(
    url: str,
    timeout: int,
    headers: dict[str, str] | None = None,
    *,
    cache_ttl_seconds: int = 0,
    cache_dir: Path | None = None,
    cache_events: list[dict[str, Any]] | None = None,
    refresh: bool = False,
) -> bytes:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    cache_path: Path | None = None
    if cache_ttl_seconds > 0 and cache_dir is not None:
        cache_path = cache_dir / f"{cache_key(url, request_headers)}.body"
        if cache_path.exists() and not refresh:
            age_seconds = max(0.0, time.time() - cache_path.stat().st_mtime)
            if age_seconds <= cache_ttl_seconds:
                record_cache_event(cache_events, "hit", url, age_seconds)
                return cache_path.read_bytes()
            record_cache_event(cache_events, "stale", url, age_seconds)
        else:
            record_cache_event(cache_events, "miss", url)
    req = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("wb", dir=str(cache_path.parent), delete=False) as tmp:
            tmp.write(body)
            tmp_path = Path(tmp.name)
        tmp_path.replace(cache_path)
        record_cache_event(cache_events, "write", url)
    return body


def get_json(url: str, timeout: int, errors: list[dict[str, Any]], source: str, args: argparse.Namespace) -> Any | None:
    body = ""
    try:
        body = http_get(
            url,
            timeout,
            cache_ttl_seconds=args.cache_ttl_seconds,
            cache_dir=args.cache_dir,
            cache_events=args.cache_events,
            refresh=args.refresh,
        ).decode("utf-8")
        return json.loads(body)
    except urllib.error.HTTPError as exc:
        errors.append(http_error_record(source, exc, url))
    except urllib.error.URLError as exc:
        errors.append({"source": source, "error": f"url_error:{exc.reason}", "url": url})
    except json.JSONDecodeError as exc:
        errors.append({"source": source, "error": f"json_decode_error:{exc}", "url": url, "bodySnippet": safe_snippet(body)})
    except (TimeoutError, UnicodeDecodeError) as exc:
        errors.append({"source": source, "error": f"{type(exc).__name__}:{exc}", "url": url})
    return None


def limited_topics(topics: list[str], max_topics: int = 4) -> list[str]:
    return topics[:max_topics] if topics else DEFAULT_TOPICS[:max_topics]


def build_topic_query(topics: list[str], max_topics: int = 5) -> str:
    parts = []
    for topic in limited_topics(topics, max_topics=max_topics):
        if " " in topic:
            parts.append(f'"{topic}"')
        else:
            parts.append(topic)
    return " OR ".join(parts)


def default_cache_dir() -> Path:
    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    root = Path(xdg_cache_home) if xdg_cache_home else Path.home() / ".cache"
    return root / "agent-kit" / "topic-radar"


def cache_key(url: str, headers: dict[str, str] | None) -> str:
    cache_input = json.dumps({"url": url, "headers": headers or {}}, sort_keys=True).encode("utf-8")
    return hashlib.sha256(cache_input).hexdigest()


def record_cache_event(events: list[dict[str, Any]] | None, status: str, url: str, age_seconds: float | None = None) -> None:
    if events is None:
        return
    parsed = urllib.parse.urlsplit(url)
    event: dict[str, Any] = {
        "status": status,
        "host": parsed.netloc,
        "path": parsed.path[:120],
    }
    if age_seconds is not None:
        event["ageSeconds"] = round(age_seconds, 1)
    events.append(event)


def safe_snippet(value: bytes | str, limit: int = 240) -> str:
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    return normalize_space(text[:limit])


def http_error_record(
    source: str,
    exc: urllib.error.HTTPError,
    url: str,
    *,
    source_detail: str | None = None,
) -> dict[str, Any]:
    body = b""
    try:
        body = exc.read(512)
    except Exception:  # noqa: BLE001 - diagnostic best effort.
        body = b""
    record: dict[str, Any] = {
        "source": source,
        "error": f"http_error:{exc.code}",
        "url": url,
    }
    if source_detail:
        record["sourceDetail"] = source_detail
    content_type = exc.headers.get("content-type") if exc.headers else None
    if content_type:
        record["contentType"] = content_type
    snippet = safe_snippet(body)
    if snippet:
        record["bodySnippet"] = snippet
    return record


def load_json_path(path_value: str, errors: list[dict[str, Any]], source: str, source_detail: str) -> Any | None:
    try:
        if path_value == "-":
            text = sys.stdin.read()
        else:
            text = Path(path_value).read_text(encoding="utf-8")
        return json.loads(text)
    except FileNotFoundError:
        errors.append({"source": source, "sourceDetail": source_detail, "error": "json_file_not_found", "path": path_value})
    except PermissionError:
        errors.append({"source": source, "sourceDetail": source_detail, "error": "json_file_permission_denied", "path": path_value})
    except json.JSONDecodeError as exc:
        errors.append({"source": source, "sourceDetail": source_detail, "error": f"invalid_json:{exc}", "path": path_value})
    return None


def maybe_parse_json_text(value: Any) -> Any | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text[0] not in "[{":
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def looks_like_polymarket_record(value: dict[str, Any]) -> bool:
    keys = {
        "id",
        "slug",
        "title",
        "question",
        "volume",
        "volume24hr",
        "volume1wk",
        "liquidity",
        "clobTokenIds",
        "clob_token_ids",
    }
    return bool(keys.intersection(value.keys()))


def infer_polymarket_kind(record: dict[str, Any], default_kind: str) -> str:
    if record.get("question") or record.get("conditionId") or record.get("condition_id"):
        return "markets"
    if isinstance(record.get("markets"), list):
        return "events"
    return default_kind


def iter_polymarket_mcp_records(
    payload: Any,
    *,
    default_kind: str = "mcp",
    source_detail: str = POLYMARKET_MCP_SOURCE_DETAIL,
) -> list[tuple[str, str, dict[str, Any]]]:
    parsed_text = maybe_parse_json_text(payload)
    if parsed_text is not None:
        return iter_polymarket_mcp_records(parsed_text, default_kind=default_kind, source_detail=source_detail)

    records: list[tuple[str, str, dict[str, Any]]] = []
    if isinstance(payload, list):
        for item in payload:
            records.extend(iter_polymarket_mcp_records(item, default_kind=default_kind, source_detail=source_detail))
        return records

    if not isinstance(payload, dict):
        return records

    for text_key in ("result", "text"):
        parsed = maybe_parse_json_text(payload.get(text_key))
        if parsed is not None:
            records.extend(iter_polymarket_mcp_records(parsed, default_kind=default_kind, source_detail=source_detail))

    if isinstance(payload.get("content"), list):
        records.extend(
            iter_polymarket_mcp_records(
                payload["content"],
                default_kind=default_kind,
                source_detail=source_detail,
            )
        )

    keyed_children = {
        "events": "events",
        "eventResults": "events",
        "gamma_list_events": "events",
        "markets": "markets",
        "marketResults": "markets",
        "gamma_list_markets": "markets",
        "results": default_kind,
        "search": "search",
        "searchResults": "search",
        "gamma_search_public": "search",
    }
    for key, kind in keyed_children.items():
        if key in payload:
            records.extend(
                iter_polymarket_mcp_records(
                    payload[key],
                    default_kind=kind,
                    source_detail=f"{source_detail}/{key}",
                )
            )

    if looks_like_polymarket_record(payload):
        records.append((infer_polymarket_kind(payload, default_kind), source_detail, payload))
    return records


def polymarket_url(kind: str, record: dict[str, Any]) -> str:
    url = normalize_space(record.get("url") or record.get("link") or record.get("marketUrl") or record.get("eventUrl"))
    if url:
        return url
    slug = normalize_space(record.get("slug"))
    if not slug:
        return ""
    path = "market" if kind == "markets" else "event"
    return f"https://polymarket.com/{path}/{slug}"


def polymarket_metric(record: dict[str, Any]) -> tuple[str, float]:
    for key in (
        "volume24hr",
        "volume1wk",
        "volume1mo",
        "volume",
        "liquidity",
        "liquidityClob",
        "openInterest",
    ):
        value = as_float(record.get(key))
        if value:
            return key, value
    return "mcp_discovery", 0.0


def polymarket_record_to_item(kind: str, source_detail: str, record: dict[str, Any]) -> RadarItem | None:
    title = normalize_space(record.get("title") or record.get("question") or record.get("name") or record.get("slug"))
    if not title:
        return None
    metric, value = polymarket_metric(record)
    published = (
        record.get("updatedAt")
        or record.get("updated_at")
        or record.get("startDate")
        or record.get("start_date")
        or iso_now()
    )
    return RadarItem(
        source="polymarket",
        source_detail=source_detail,
        title=title,
        url=polymarket_url(kind, record),
        published_at=str(published) if published else iso_now(),
        engagement=value,
        reason=f"MCP {metric} {format_number(value)}" if value else "MCP discovery result",
        raw={
            "id": record.get("id"),
            "slug": record.get("slug"),
            "kind": kind,
            "metric": metric,
            "endDate": record.get("endDate") or record.get("end_date"),
            "clobTokenIds": record.get("clobTokenIds") or record.get("clob_token_ids"),
        },
    )


def fetch_polymarket_mcp_json(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    if not args.polymarket_mcp_json:
        return []
    payload = load_json_path(args.polymarket_mcp_json, errors, "polymarket", "mcp-json")
    if payload is None:
        return []
    records = iter_polymarket_mcp_records(payload)
    items: list[RadarItem] = []
    seen: set[tuple[str, str]] = set()
    for kind, source_detail, record in records:
        item = polymarket_record_to_item(kind, source_detail, record)
        if item is None:
            continue
        key = (item.url, item.title)
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
        if len(items) >= args.limit:
            break
    if not items:
        errors.append(
            {
                "source": "polymarket",
                "sourceDetail": "mcp-json",
                "error": "mcp_json_no_usable_records",
                "path": args.polymarket_mcp_json,
            }
        )
    return items


def fetch_polymarket_helper(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    skill_dir = Path(__file__).resolve().parents[1]
    script = skill_dir.parent / "polymarket-readonly/scripts/polymarket-readonly.sh"
    if not script.exists():
        errors.append({"source": "polymarket", "error": "helper_not_found", "path": str(script)})
        return []
    proc = subprocess.run(
        [str(script), "--report", args.report, "--scope", "both", "--format", "json", "--limit", str(args.limit)],
        text=True,
        capture_output=True,
        timeout=args.timeout + 10,
    )
    if proc.returncode == 3:
        errors.append({"source": "polymarket", "error": "unsafe_trading_credential_environment", "unsafe": True})
        return []
    if proc.returncode != 0:
        errors.append({"source": "polymarket", "error": "helper_failed", "stderr": proc.stderr.strip()})
        return []
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        errors.append({"source": "polymarket", "error": f"invalid_json:{exc}"})
        return []
    generated_at = payload.get("generatedAt")
    items: list[RadarItem] = []
    sections = payload.get("sections") or {}
    for section_name in ("events", "markets"):
        section = sections.get(section_name) or {}
        for result in section.get("results") or []:
            title = result.get("title") or result.get("question") or result.get("slug") or "Untitled Polymarket signal"
            ranking_value = as_float(result.get("rankingValue"))
            metric = section.get("rankingMetric") or payload.get("rankingMetric")
            items.append(
                RadarItem(
                    source="polymarket",
                    source_detail=f"gamma-api/{section_name}",
                    title=normalize_space(title),
                    url=result.get("url") or "",
                    published_at=generated_at,
                    engagement=ranking_value,
                    reason=f"{metric} ranking value {format_number(ranking_value)}",
                    raw={
                        "slug": result.get("slug"),
                        "rankingMetric": metric,
                        "rankingMode": section.get("rankingMode") or payload.get("rankingMode"),
                    },
                )
            )
    return items


def fetch_polymarket(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    mcp_items = fetch_polymarket_mcp_json(args, errors)
    if mcp_items:
        return mcp_items
    if args.polymarket_mcp_json and args.polymarket_fallback == "none":
        return []
    return fetch_polymarket_helper(args, errors)


def fetch_hn(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    since_ts = int((now_utc() - timedelta(days=args.days)).timestamp())
    topics = limited_topics(args.topics)
    per_topic = max(1, math.ceil(args.limit / max(len(topics), 1)))
    items: list[RadarItem] = []
    for topic in topics:
        params = {
            "query": topic,
            "tags": "story",
            "numericFilters": f"created_at_i>{since_ts}",
            "hitsPerPage": str(per_topic),
        }
        url = f"https://hn.algolia.com/api/v1/search_by_date?{urllib.parse.urlencode(params)}"
        payload = get_json(url, args.timeout, errors, "hn", args)
        if not isinstance(payload, dict):
            continue
        for hit in payload.get("hits") or []:
            title = normalize_space(hit.get("title") or hit.get("story_title"))
            if not title:
                continue
            object_id = str(hit.get("objectID") or "")
            item_url = hit.get("url") or (f"https://news.ycombinator.com/item?id={object_id}" if object_id else "")
            points = as_float(hit.get("points"))
            comments = as_float(hit.get("num_comments"))
            item = RadarItem(
                source="hn",
                source_detail="hn.algolia.com",
                title=title,
                url=item_url,
                published_at=hit.get("created_at"),
                engagement=points + comments * 2,
                reason=f"{format_number(points)} points, {format_number(comments)} comments",
                raw={"objectID": object_id, "query": topic},
            )
            if interest_match_score(item, args.topics) > 0:
                items.append(item)
    return items


def fetch_github(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    since_date = (now_utc() - timedelta(days=max(args.days, 1))).date().isoformat()
    topics = limited_topics(args.topics)
    per_topic = max(1, math.ceil(args.limit / max(len(topics), 1)))
    items: list[RadarItem] = []
    for topic in topics:
        query = f"{topic} in:name,description,readme pushed:>={since_date} stars:>10"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": str(per_topic)}
        url = f"https://api.github.com/search/repositories?{urllib.parse.urlencode(params)}"
        payload = get_json(url, args.timeout, errors, "github", args)
        if not isinstance(payload, dict):
            continue
        for repo in payload.get("items") or []:
            title = repo.get("full_name") or repo.get("name")
            if not title:
                continue
            stars = as_float(repo.get("stargazers_count"))
            forks = as_float(repo.get("forks_count"))
            items.append(
                RadarItem(
                    source="github",
                    source_detail="api.github.com/search/repositories",
                    title=title,
                    url=repo.get("html_url") or "",
                    published_at=repo.get("pushed_at") or repo.get("updated_at"),
                    summary=normalize_space(repo.get("description")),
                    engagement=stars + forks * 3,
                    reason=f"{format_number(stars)} stars, pushed {repo.get('pushed_at') or 'unknown'}",
                    tags=repo.get("topics") or [],
                    raw={"language": repo.get("language"), "forks": forks, "query": topic},
                )
            )
    return items


def fetch_arxiv(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    query = "(cat:cs.AI OR cat:cs.CL OR cat:cs.LG)"
    params = {
        "search_query": query,
        "start": "0",
        "max_results": str(max(args.limit * 4, args.limit)),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"https://export.arxiv.org/api/query?{urllib.parse.urlencode(params)}"
    try:
        xml_bytes = http_get(
            url,
            args.timeout,
            cache_ttl_seconds=args.cache_ttl_seconds,
            cache_dir=args.cache_dir,
            cache_events=args.cache_events,
            refresh=args.refresh,
        )
    except urllib.error.HTTPError as exc:
        errors.append(http_error_record("arxiv", exc, url))
        return []
    except Exception as exc:  # noqa: BLE001 - report per-source degradation.
        errors.append({"source": "arxiv", "error": f"{type(exc).__name__}:{exc}", "url": url})
        return []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        errors.append({"source": "arxiv", "error": f"xml_parse_error:{exc}", "url": url})
        return []
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    cutoff = now_utc() - timedelta(days=max(args.days, 1) + 2)
    items: list[RadarItem] = []
    for entry in root.findall("atom:entry", ns):
        title = normalize_space(child_text(entry, "atom:title", ns))
        if not title:
            continue
        published = child_text(entry, "atom:published", ns) or child_text(entry, "atom:updated", ns)
        published_dt = parse_iso_datetime(published)
        if published_dt and published_dt < cutoff:
            continue
        summary = normalize_space(child_text(entry, "atom:summary", ns))
        link = ""
        for link_node in entry.findall("atom:link", ns):
            if link_node.attrib.get("rel") in (None, "alternate"):
                link = link_node.attrib.get("href", "")
                break
        categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ns)]
        authors = [normalize_space(child_text(node, "atom:name", ns)) for node in entry.findall("atom:author", ns)]
        items.append(
            RadarItem(
                source="arxiv",
                source_detail="export.arxiv.org/api/query",
                title=title,
                url=link,
                published_at=published,
                summary=summary[:320] if summary else None,
                engagement=0,
                reason=f"new paper in {', '.join(filter(None, categories[:3]))}",
                tags=[tag for tag in categories if tag],
                raw={"authors": [author for author in authors if author][:5]},
            )
        )
        if len(items) >= args.limit:
            break
    return items


def fetch_hf(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    params = {"sort": "trendingScore", "direction": "-1", "limit": str(max(args.limit * 2, args.limit))}
    url = f"https://huggingface.co/api/models?{urllib.parse.urlencode(params)}"
    payload = get_json(url, args.timeout, errors, "hf", args)
    if not isinstance(payload, list):
        return []
    items: list[RadarItem] = []
    for model in payload:
        model_id = model.get("modelId") or model.get("id")
        if not model_id:
            continue
        likes = as_float(model.get("likes"))
        downloads = as_float(model.get("downloads"))
        tags = [str(tag) for tag in model.get("tags") or []]
        items.append(
            RadarItem(
                source="hf",
                source_detail="huggingface.co/api/models",
                title=model_id,
                url=f"https://huggingface.co/{model_id}",
                published_at=model.get("lastModified") or model.get("createdAt"),
                summary=normalize_space(model.get("pipeline_tag") or model.get("library_name")),
                engagement=likes * 10 + math.log1p(max(downloads, 0.0)) * 10,
                reason=f"{format_number(likes)} likes, {format_number(downloads)} downloads",
                tags=tags[:12],
                raw={"pipelineTag": model.get("pipeline_tag"), "libraryName": model.get("library_name")},
            )
        )
        if len(items) >= args.limit:
            break
    return items


def fetch_official(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    items: list[RadarItem] = []
    cutoff = now_utc() - timedelta(days=max(args.days, 1) + 2)
    per_feed_limit = max(2, math.ceil(args.limit / 4))
    for feed_name, feed_url in OFFICIAL_FEEDS:
        try:
            xml_bytes = http_get(
                feed_url,
                args.timeout,
                cache_ttl_seconds=args.cache_ttl_seconds,
                cache_dir=args.cache_dir,
                cache_events=args.cache_events,
                refresh=args.refresh,
            )
        except urllib.error.HTTPError as exc:
            errors.append(http_error_record("official", exc, feed_url, source_detail=feed_name))
            continue
        except Exception as exc:  # noqa: BLE001 - report per-source degradation.
            errors.append({"source": "official", "sourceDetail": feed_name, "error": f"{type(exc).__name__}:{exc}"})
            continue
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as exc:
            errors.append({"source": "official", "sourceDetail": feed_name, "error": f"xml_parse_error:{exc}"})
            continue
        entries = parse_feed_entries(root)
        feed_item_count = 0
        for entry in entries:
            published = entry.get("publishedAt")
            published_dt = parse_iso_datetime(published)
            if published_dt and published_dt < cutoff:
                continue
            title = normalize_space(entry.get("title"))
            if not title:
                continue
            item = RadarItem(
                source="official",
                source_detail=feed_name,
                title=title,
                url=entry.get("url") or feed_url,
                published_at=published,
                summary=normalize_space(entry.get("summary"))[:320] or None,
                engagement=0,
                reason=f"official source: {feed_name}",
                raw={"feed": feed_url},
            )
            if interest_match_score(item, args.topics) > 0 or feed_name in ("OpenAI News", "Anthropic News"):
                items.append(item)
                feed_item_count += 1
            if feed_item_count >= per_feed_limit:
                break
    for page_name, page_url, base_url in OFFICIAL_HTML_PAGES:
        try:
            html_bytes = http_get(
                page_url,
                args.timeout,
                cache_ttl_seconds=args.cache_ttl_seconds,
                cache_dir=args.cache_dir,
                cache_events=args.cache_events,
                refresh=args.refresh,
            )
        except urllib.error.HTTPError as exc:
            errors.append(http_error_record("official", exc, page_url, source_detail=page_name))
            continue
        except Exception as exc:  # noqa: BLE001 - report per-source degradation.
            errors.append({"source": "official", "sourceDetail": page_name, "error": f"{type(exc).__name__}:{exc}"})
            continue
        entries = parse_official_page_links(html_bytes.decode("utf-8", errors="replace"), "/news/", base_url)
        page_item_count = 0
        for entry in entries:
            published = entry.get("publishedAt")
            published_dt = parse_iso_datetime(published)
            if published_dt and published_dt < cutoff:
                continue
            item = RadarItem(
                source="official",
                source_detail=page_name,
                title=entry.get("title") or "",
                url=entry.get("url") or page_url,
                published_at=published,
                summary=truncate(entry.get("summary"), 320) or None,
                engagement=0,
                reason=f"official source: {page_name}",
                raw={"page": page_url},
            )
            if interest_match_score(item, args.topics) > 0:
                items.append(item)
                page_item_count += 1
            if page_item_count >= per_feed_limit:
                break
    return items


def fetch_news(args: argparse.Namespace, errors: list[dict[str, Any]]) -> list[RadarItem]:
    if args.news_provider == "google":
        return fetch_google_news_rss(args, errors, "Google News RSS selected")
    query = build_topic_query(args.topics)
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "sort": "datedesc",
        "timespan": f"{max(args.days, 1)}d",
        "maxrecords": str(args.limit),
    }
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?{urllib.parse.urlencode(params)}"
    payload = get_json(url, args.timeout, errors, "news", args)
    if not isinstance(payload, dict):
        if args.news_provider == "gdelt":
            return []
        return fetch_google_news_rss(args, errors, "GDELT unavailable")
    items: list[RadarItem] = []
    for article in payload.get("articles") or []:
        title = normalize_space(article.get("title"))
        if not title:
            continue
        domain = article.get("domain") or article.get("sourceCommonName")
        seendate = parse_compact_gdelt_datetime(article.get("seendate") or article.get("date"))
        item = RadarItem(
            source="news",
            source_detail="GDELT DOC API",
            title=title,
            url=article.get("url") or "",
            published_at=seendate,
            summary=normalize_space(article.get("snippet")) or None,
            engagement=0,
            reason=f"matched GDELT query on {domain or 'unknown domain'}",
            raw={
                "domain": domain,
                "language": article.get("language"),
                "sourceCountry": article.get("sourceCountry"),
                "query": query,
            },
        )
        if interest_match_score(item, args.topics) > 0:
            items.append(item)
    if not items:
        if args.news_provider == "gdelt":
            return []
        return fetch_google_news_rss(args, errors, "GDELT returned no articles")
    return items


def fetch_google_news_rss(
    args: argparse.Namespace,
    errors: list[dict[str, Any]],
    fallback_reason: str,
) -> list[RadarItem]:
    query = f"{build_topic_query(args.topics, max_topics=3)} when:{max(args.days, 1)}d"
    params = {
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }
    url = f"https://news.google.com/rss/search?{urllib.parse.urlencode(params)}"
    try:
        xml_bytes = http_get(
            url,
            args.timeout,
            cache_ttl_seconds=args.cache_ttl_seconds,
            cache_dir=args.cache_dir,
            cache_events=args.cache_events,
            refresh=args.refresh,
        )
    except urllib.error.HTTPError as exc:
        errors.append(http_error_record("news", exc, url, source_detail="Google News RSS"))
        return []
    except Exception as exc:  # noqa: BLE001 - report per-source degradation.
        errors.append({"source": "news", "sourceDetail": "Google News RSS", "error": f"{type(exc).__name__}:{exc}"})
        return []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        errors.append({"source": "news", "sourceDetail": "Google News RSS", "error": f"xml_parse_error:{exc}"})
        return []
    cutoff = now_utc() - timedelta(days=max(args.days, 1) + 1)
    items: list[RadarItem] = []
    for entry in parse_feed_entries(root):
        title = normalize_space(entry.get("title"))
        if not title:
            continue
        published = entry.get("publishedAt")
        published_dt = parse_iso_datetime(published)
        if published_dt and published_dt < cutoff:
            continue
        item = RadarItem(
            source="news",
            source_detail="Google News RSS",
            title=title,
            url=entry.get("url") or "",
            published_at=published,
            summary=normalize_space(entry.get("summary")) or None,
            engagement=0,
            reason=f"{fallback_reason}; matched Google News RSS",
            raw={"query": query},
        )
        if interest_match_score(item, args.topics) == 0:
            continue
        items.append(item)
        if len(items) >= args.limit:
            break
    return items


def child_text(node: ET.Element, path: str, ns: dict[str, str]) -> str:
    child = node.find(path, ns)
    return child.text if child is not None and child.text else ""


def parse_feed_entries(root: ET.Element) -> list[dict[str, str]]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        link = child_text_no_ns(item, "link")
        entries.append(
            {
                "title": child_text_no_ns(item, "title"),
                "url": link,
                "publishedAt": child_text_no_ns(item, "pubDate") or child_text_no_ns(item, "date"),
                "summary": strip_html_text(child_text_no_ns(item, "description")),
            }
        )
    for entry in root.findall("atom:entry", ns):
        link = ""
        for link_node in entry.findall("atom:link", ns):
            if link_node.attrib.get("rel") in (None, "alternate"):
                link = link_node.attrib.get("href", "")
                break
        entries.append(
            {
                "title": child_text(entry, "atom:title", ns),
                "url": link,
                "publishedAt": child_text(entry, "atom:published", ns) or child_text(entry, "atom:updated", ns),
                "summary": strip_html_text(child_text(entry, "atom:summary", ns)),
            }
        )
    return entries


def parse_official_page_links(html_text: str, href_prefix: str, base_url: str) -> list[dict[str, str]]:
    parser = LinkTextParser(href_prefix)
    parser.feed(html_text)
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for href, text in parser.links:
        if href in seen:
            continue
        seen.add(href)
        parsed = parse_official_page_text(text)
        if not parsed["title"]:
            continue
        entries.append(
            {
                "title": parsed["title"],
                "summary": parsed["summary"],
                "publishedAt": parsed["publishedAt"],
                "url": urllib.parse.urljoin(base_url, href),
            }
        )
    return entries


def parse_official_page_text(text: str) -> dict[str, str]:
    cleaned = normalize_space(text)
    date_match = re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b", cleaned)
    if not date_match:
        return {"title": strip_official_categories(cleaned), "summary": "", "publishedAt": ""}
    date_text = date_match.group(0)
    before = strip_official_categories(cleaned[: date_match.start()].strip())
    after = strip_official_categories(cleaned[date_match.end() :].strip())
    title = before or after
    summary = after if before and after else ""
    return {"title": title, "summary": summary, "publishedAt": parse_month_date(date_text)}


def strip_official_categories(value: str) -> str:
    text = normalize_space(value)
    changed = True
    while changed:
        changed = False
        for category in OFFICIAL_PAGE_CATEGORIES:
            if text == category:
                return ""
            if text.startswith(f"{category} "):
                text = text[len(category) + 1 :].strip()
                changed = True
            if text.endswith(f" {category}"):
                text = text[: -(len(category) + 1)].strip()
                changed = True
    return text


def parse_month_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%b %d, %Y").replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        return value


def child_text_no_ns(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    if child is not None and child.text:
        return child.text
    for candidate in node:
        if candidate.tag.endswith(f"}}{tag}") and candidate.text:
            return candidate.text
    return ""


def as_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def format_number(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}"


def parse_sources(value: str) -> list[str]:
    requested = [part.strip().lower() for part in value.split(",") if part.strip()]
    if not requested:
        return DEFAULT_SOURCES.copy()
    resolved: list[str] = []
    for source in requested:
        canonical = SOURCE_ALIASES.get(source)
        if canonical is None:
            raise UsageError(f"unknown source: {source}")
        if canonical == "all":
            return DEFAULT_SOURCES.copy()
        if canonical not in resolved:
            resolved.append(canonical)
    return resolved


def sample_items() -> list[RadarItem]:
    return [
        RadarItem(
            source="official",
            source_detail="OpenAI News",
            title="New agent model release for long-running coding tasks",
            url="https://openai.com/news/example-agent-model",
            published_at=iso_now(),
            summary="Official release notes describe improved long-running task reliability.",
            engagement=0,
            reason="official source: OpenAI News",
        ),
        RadarItem(
            source="hn",
            source_detail="hn.algolia.com",
            title="Show HN: Local AI agent runtime with durable task memory",
            url="https://news.ycombinator.com/item?id=1",
            published_at=iso_now(),
            engagement=340,
            reason="220 points, 60 comments",
        ),
        RadarItem(
            source="github",
            source_detail="api.github.com/search/repositories",
            title="example/agent-runtime",
            url="https://github.com/example/agent-runtime",
            published_at=iso_now(),
            summary="A local-first AI agent runtime for developer workflows.",
            engagement=2400,
            reason="2.10K stars, pushed today",
            tags=["ai-agents", "developer-tools"],
        ),
        RadarItem(
            source="arxiv",
            source_detail="export.arxiv.org/api/query",
            title="Evaluating Long-Running AI Agents in Real Developer Workflows",
            url="https://arxiv.org/abs/2605.00000",
            published_at=iso_now(),
            summary="A benchmark for agent reliability over multi-hour coding tasks.",
            reason="new paper in cs.AI",
            tags=["cs.AI"],
        ),
        RadarItem(
            source="hf",
            source_detail="huggingface.co/api/models",
            title="example/agentic-code-model",
            url="https://huggingface.co/example/agentic-code-model",
            published_at=iso_now(),
            engagement=900,
            reason="90 likes, 10.00K downloads",
            tags=["text-generation", "agents"],
        ),
        RadarItem(
            source="polymarket",
            source_detail="gamma-api/events",
            title="Will a major AI lab release a new frontier model this month?",
            url="https://polymarket.com/event/example-ai-release",
            published_at=iso_now(),
            engagement=120000,
            reason="volume24hr ranking value 120.00K",
        ),
        RadarItem(
            source="news",
            source_detail="GDELT DOC API",
            title="AI agent startups draw new infrastructure investment",
            url="https://example.com/ai-agent-investment",
            published_at=iso_now(),
            reason="matched GDELT query on example.com",
        ),
    ]


def gather(args: argparse.Namespace) -> tuple[list[RadarItem], dict[str, list[RadarItem]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if args.sample:
        items = [item for item in sample_items() if item.source in args.sources]
        sections = group_by_source(items)
        ranked = dedupe_and_rank(items, args.topics, args.days)
        return ranked, sections, errors

    fetchers = {
        "polymarket": fetch_polymarket,
        "hn": fetch_hn,
        "github": fetch_github,
        "arxiv": fetch_arxiv,
        "hf": fetch_hf,
        "official": fetch_official,
        "news": fetch_news,
    }
    all_items: list[RadarItem] = []
    sections: dict[str, list[RadarItem]] = {source: [] for source in args.sources}

    def fetch_source(source: str) -> tuple[str, list[RadarItem], list[dict[str, Any]]]:
        source_errors: list[dict[str, Any]] = []
        try:
            return source, fetchers[source](args, source_errors), source_errors
        except Exception as exc:  # noqa: BLE001 - isolate per-source failures.
            source_errors.append({"source": source, "error": f"unexpected_error:{type(exc).__name__}:{exc}"})
            return source, [], source_errors

    if args.jobs <= 1 or len(args.sources) <= 1:
        results = [fetch_source(source) for source in args.sources]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(args.sources))) as executor:
            future_to_source = {executor.submit(fetch_source, source): source for source in args.sources}
            for future in as_completed(future_to_source):
                results.append(future.result())

    for source, source_items, source_errors in results:
        sections[source] = dedupe_and_rank(source_items, args.topics, args.days)
        all_items.extend(source_items)
        errors.extend(source_errors)
    ranked = dedupe_and_rank(all_items, args.topics, args.days)
    return ranked, sections, errors


def group_by_source(items: list[RadarItem]) -> dict[str, list[RadarItem]]:
    sections: dict[str, list[RadarItem]] = {}
    for item in items:
        sections.setdefault(item.source, []).append(item)
    return sections


def item_search_text(item: RadarItem) -> str:
    return " ".join(
        [
            item.source,
            item.source_detail or "",
            item.title,
            item.summary or "",
            item.reason,
            " ".join(item.tags),
        ]
    ).lower()


def classify_brief_cluster(item: RadarItem) -> str:
    haystack = item_search_text(item)
    for cluster_name, keywords in BRIEF_CLUSTERS:
        if any(keyword in haystack for keyword in keywords):
            return cluster_name
    return OTHER_BRIEF_CLUSTER


def build_brief_clusters(args: argparse.Namespace, ranked: list[RadarItem]) -> list[dict[str, Any]]:
    grouped: dict[str, list[RadarItem]] = {name: [] for name, _ in BRIEF_CLUSTERS}
    grouped[OTHER_BRIEF_CLUSTER] = []
    for item in ranked[: args.limit]:
        grouped[classify_brief_cluster(item)].append(item)
    clusters: list[dict[str, Any]] = []
    for cluster_name in [name for name, _ in BRIEF_CLUSTERS] + [OTHER_BRIEF_CLUSTER]:
        cluster_items = grouped.get(cluster_name) or []
        if cluster_items:
            clusters.append({"name": cluster_name, "items": cluster_items})
    return clusters


def cache_metadata(args: argparse.Namespace) -> dict[str, Any]:
    events = getattr(args, "cache_events", [])
    counts: dict[str, int] = {}
    for event in events:
        status = str(event.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return {
        "enabled": bool(args.cache_ttl_seconds and not args.sample),
        "ttlMinutes": args.cache_ttl_minutes,
        "refresh": args.refresh,
        "events": counts,
    }


def render_json(
    args: argparse.Namespace,
    ranked: list[RadarItem],
    sections: dict[str, list[RadarItem]],
    errors: list[dict[str, Any]],
) -> str:
    payload = {
        "ok": not any(error.get("unsafe") for error in errors),
        "version": VERSION,
        "preset": args.preset,
        "profile": args.profile,
        "report": args.report,
        "windowDays": args.days,
        "generatedAt": iso_now(),
        "topics": args.topics,
        "sources": args.sources,
        "newsProvider": args.news_provider,
        "ranking": {
            "mode": "heuristic",
            "note": "Score combines source weight, engagement, recency, topic match, and cross-source duplication.",
        },
        "brief": {
            "enabled": args.brief,
            "clusters": [
                {"name": cluster["name"], "items": [item.to_json() for item in cluster["items"]]}
                for cluster in build_brief_clusters(args, ranked)
            ]
            if args.brief
            else [],
        },
        "cache": cache_metadata(args),
        "items": [item.to_json() for item in ranked[: args.limit]],
        "sections": {
            source: [item.to_json() for item in dedupe_and_rank(items, args.topics, args.days)[: args.limit]]
            for source, items in sections.items()
        },
        "errors": errors,
        "sample": args.sample,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def render_markdown(
    args: argparse.Namespace,
    ranked: list[RadarItem],
    sections: dict[str, list[RadarItem]],
    errors: list[dict[str, Any]],
) -> str:
    title_report = args.report.title()
    lines = [
        f"# AI/Tech Topic Radar {title_report}",
        "",
        f"- Generated: {iso_now()}",
        f"- Window: {args.days} day(s)",
        f"- Preset: `{args.preset}`",
        f"- Profile: `{args.profile}`",
        f"- Topics: {', '.join(args.topics)}",
        f"- Sources: {', '.join(args.sources)}",
        f"- News provider: `{args.news_provider}`",
        f"- Cache: {render_cache_line(args)}",
        "- Ranking: heuristic source weight + engagement + recency + topic match + cross-source bonus",
        "",
    ]
    if args.brief:
        lines.extend(render_brief_markdown(args, ranked))
    lines.extend(["## Top Signals", ""])
    if not ranked:
        lines.append("- No matching signals found.")
    for item in ranked[: args.limit]:
        lines.append(render_item_bullet(item))

    lines.extend(["", "## Source Sections", ""])
    for source in args.sources:
        section_items = sections.get(source, [])
        label = SOURCE_LABELS.get(source, source)
        lines.extend([f"### {label}", ""])
        if not section_items:
            lines.append("- No matching signals.")
        else:
            for item in dedupe_and_rank(section_items, args.topics, args.days)[: args.limit]:
                lines.append(render_item_bullet(item))
        lines.append("")

    if errors:
        lines.extend(["## Source Errors", ""])
        for error in errors:
            source = error.get("source", "unknown")
            detail = error.get("sourceDetail")
            where = f"{source}/{detail}" if detail else source
            snippet = truncate(str(error.get("bodySnippet") or ""), 160)
            suffix = f" | snippet: {snippet}" if snippet else ""
            lines.append(f"- `{where}`: {error.get('error', 'unknown_error')}{suffix}")
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- Read-only public/source lookups; no posting, trading, signing, or credentialed actions.",
            "- Scores are heuristic triage signals, not objective importance or investment advice.",
            "- Follow source links before treating an item as confirmed-current.",
        ]
    )
    return "\n".join(lines)


def render_cache_line(args: argparse.Namespace) -> str:
    metadata = cache_metadata(args)
    if not metadata["enabled"]:
        return "disabled"
    events = metadata["events"]
    if not events:
        return f"enabled, ttl {metadata['ttlMinutes']} minute(s)"
    counts = ", ".join(f"{key}={value}" for key, value in sorted(events.items()))
    return f"enabled, ttl {metadata['ttlMinutes']} minute(s), {counts}"


def render_brief_markdown(args: argparse.Namespace, ranked: list[RadarItem]) -> list[str]:
    lines = ["## Brief", ""]
    clusters = build_brief_clusters(args, ranked)
    if not clusters:
        return lines + ["- No matching signals found.", ""]
    for cluster in clusters:
        lines.extend([f"### {cluster['name']}", ""])
        for item in cluster["items"]:
            lines.append(render_brief_bullet(item))
        lines.append("")
    return lines


def render_brief_bullet(item: RadarItem) -> str:
    date = short_date(item.published_at)
    source = SOURCE_LABELS.get(item.source, item.source)
    link = f"[{escape_md(item.title)}]({item.url})" if item.url else escape_md(item.title)
    summary = truncate(item.summary, 180)
    suffix = f" - {summary}" if summary else ""
    return f"- {date} {link} | `{source}`{suffix}"


def render_item_bullet(item: RadarItem) -> str:
    score = f"{item.score:.1f}"
    source = SOURCE_LABELS.get(item.source, item.source)
    link = f"[{escape_md(item.title)}]({item.url})" if item.url else escape_md(item.title)
    detail = f" | {item.reason}" if item.reason else ""
    seen = f" | also: {', '.join(item.also_seen_in)}" if item.also_seen_in else ""
    return f"- {link} | `{source}` | score: {score}{detail}{seen}"


def escape_md(value: str) -> str:
    return value.replace("[", "\\[").replace("]", "\\]")


def truncate(value: str | None, limit: int) -> str:
    text = normalize_space(value)
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 3)].rstrip()}..."


def short_date(value: str | None) -> str:
    parsed = parse_iso_datetime(value)
    if parsed is None:
        return "unknown-date"
    return parsed.date().isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="topic-radar.sh",
        description="Read-only AI/technology trend radar from multiple public sources.",
    )
    parser.add_argument(
        "--preset",
        default="radar",
        help="Workflow preset: radar or ai-news. Aliases: daily, news, ai.",
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help="Topic profile to use: terry-ai-tech, ai-tech, or aliases personal/terry/default.",
    )
    parser.add_argument("--topic", action="append", dest="topics", help="Topic of interest. Repeatable.")
    parser.add_argument(
        "--sources",
        help="Comma-separated sources: all,polymarket,hn,github,arxiv,hf,official,news. Defaults to the preset.",
    )
    parser.add_argument(
        "--polymarket-mcp-json",
        help="Path to JSON exported from Polymarket MCP tool results. Used before helper fallback.",
    )
    parser.add_argument(
        "--polymarket-fallback",
        choices=["helper", "none"],
        default="helper",
        help="Fallback behavior when --polymarket-mcp-json has no usable records.",
    )
    parser.add_argument("--report", choices=["daily", "weekly"], default="daily", help="Report cadence.")
    parser.add_argument("--days", type=int, help="Window in days. Defaults to report cadence.")
    parser.add_argument("--limit", type=int, help="Maximum items per source and top section. Defaults to the preset.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format.")
    parser.add_argument("--timeout", type=int, help="Per-request timeout in seconds. Defaults to the preset.")
    parser.add_argument(
        "--brief",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include clustered brief output. Defaults to the preset.",
    )
    parser.add_argument("--jobs", type=int, help="Maximum parallel source fetches. Defaults to the source count.")
    parser.add_argument(
        "--cache-ttl-minutes",
        type=int,
        help="Public response cache TTL in minutes. Defaults to the preset.",
    )
    parser.add_argument(
        "--news-provider",
        choices=["auto", "gdelt", "google"],
        help="News provider strategy. Defaults to the preset.",
    )
    parser.add_argument("--refresh", action="store_true", help="Bypass existing cache entries and rewrite them.")
    parser.add_argument("--no-cache", action="store_true", help="Disable public response caching for this run.")
    parser.add_argument("--sample", action="store_true", help="Emit deterministic sample data without network calls.")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    return parser


def normalize_args(argv: list[str]) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(VERSION)
        raise SystemExit(0)
    requested_preset = normalize_space(args.preset).lower()
    args.preset = PRESET_ALIASES.get(requested_preset, requested_preset)
    if args.preset not in PRESETS:
        available = ", ".join(sorted(PRESETS))
        raise UsageError(f"unknown preset: {requested_preset} (available: {available})")
    preset = PRESETS[args.preset]
    requested_profile = normalize_space(args.profile).lower()
    args.profile = PROFILE_ALIASES.get(requested_profile, requested_profile)
    if args.profile not in PROFILE_TOPICS:
        available = ", ".join(sorted(PROFILE_TOPICS))
        raise UsageError(f"unknown profile: {requested_profile} (available: {available})")
    profile_topics = PROFILE_TOPICS[args.profile]
    default_topics = preset["topics"] or profile_topics
    args.topics = [normalize_space(topic) for topic in (args.topics or default_topics) if normalize_space(topic)]
    if not args.topics:
        raise UsageError("at least one topic is required")
    args.sources = parse_sources(args.sources) if args.sources else list(preset["sources"])
    if args.days is None:
        args.days = int(preset["days"] or (1 if args.report == "daily" else 7))
    if args.limit is None:
        args.limit = int(preset["limit"])
    if args.timeout is None:
        args.timeout = int(preset["timeout"])
    if args.brief is None:
        args.brief = bool(preset["brief"])
    if args.jobs is None:
        args.jobs = min(max(len(args.sources), 1), 6)
    cache_ttl_minutes = args.cache_ttl_minutes
    if cache_ttl_minutes is None:
        cache_ttl_minutes = int(preset["cache_ttl_minutes"])
    if args.no_cache or args.sample:
        cache_ttl_minutes = 0
    args.cache_ttl_minutes = cache_ttl_minutes
    args.cache_ttl_seconds = cache_ttl_minutes * 60
    args.cache_dir = default_cache_dir()
    args.cache_events = []
    if args.news_provider is None:
        args.news_provider = str(preset["news_provider"])
    if args.days < 1 or args.days > 31:
        raise UsageError("--days must be between 1 and 31")
    if args.limit < 1 or args.limit > 50:
        raise UsageError("--limit must be between 1 and 50")
    if args.timeout < 1 or args.timeout > 120:
        raise UsageError("--timeout must be between 1 and 120")
    if args.jobs < 1 or args.jobs > 16:
        raise UsageError("--jobs must be between 1 and 16")
    if args.cache_ttl_minutes < 0 or args.cache_ttl_minutes > 1440:
        raise UsageError("--cache-ttl-minutes must be between 0 and 1440")
    return args


def main(argv: list[str]) -> int:
    try:
        args = normalize_args(argv)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        return int(exc.code or 0)

    ranked, sections, errors = gather(args)
    if args.format == "json":
        print(render_json(args, ranked, sections, errors))
    else:
        print(render_markdown(args, ranked, sections, errors))
    if any(error.get("unsafe") for error in errors):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
