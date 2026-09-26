"""
Web search: Brave Search API primary, ddgs fallback.

Brave: official API with a key, full safe search control including
       off for images.
ddgs:  free, no key, but is a toss up which service it uses and
       each service may or may not support safe search off.

If BRAVE_API_KEY is not set, everything falls back to ddgs silently.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum

import httpx
from ddgs import DDGS
from ddgs.exceptions import DDGSException

logger = logging.getLogger(__name__)

BRAVE_API_KEY: str = os.getenv("BRAVE_API_KEY", "")
BRAVE_ENDPOINT: str = "https://api.search.brave.com/res/v1"


class SearchType(Enum):
    WEB = "web"
    IMAGE = "image"
    NEWS = "news"
    VIDEO = "video"


class SafeSearch(Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    OFF = "off"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    thumbnail_url: str | None = None
    published: str | None = None
    duration: str | None = None


# ═══════════════════════════════════════════════════════════════════════
# Brave Search
# ═══════════════════════════════════════════════════════════════════════

_BRAVE_ENDPOINTS = {
    SearchType.WEB:   f"{BRAVE_ENDPOINT}/web/search",
    SearchType.IMAGE: f"{BRAVE_ENDPOINT}/images/search",
    SearchType.NEWS:  f"{BRAVE_ENDPOINT}/news/search",
    SearchType.VIDEO: f"{BRAVE_ENDPOINT}/videos/search",
}

_BRAVE_SAFE_MAP = {
    SafeSearch.STRICT: "strict",
    SafeSearch.MODERATE: "moderate",
    SafeSearch.OFF: "off",
}


def _brave_search(
    query: str,
    search_type: SearchType,
    safe_search: SafeSearch,
    count: int,
) -> list[SearchResult] | None:
    """
    Try Brave Search. Returns None if not configured or on failure,
    so caller can fall back to ddgs.
    """
    if not BRAVE_API_KEY:
        return None

    url = _BRAVE_ENDPOINTS[search_type]
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    params = {
        "q": query,
        "count": min(count, 20),
        "safesearch": _BRAVE_SAFE_MAP[safe_search],
    }

    try:
        resp = httpx.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []

        if search_type == SearchType.WEB:
            for item in data.get("web", {}).get("results", [])[:count]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                ))

        elif search_type == SearchType.IMAGE:
            for item in data.get("results", [])[:count]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("properties", {}).get("url", "") or item.get("url", ""),
                    snippet=item.get("source", ""),
                    thumbnail_url=item.get("thumbnail", {}).get("src"),
                ))

        elif search_type == SearchType.NEWS:
            for item in data.get("results", [])[:count]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    published=item.get("age", ""),
                ))

        elif search_type == SearchType.VIDEO:
            for item in data.get("results", [])[:count]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    thumbnail_url=item.get("thumbnail", {}).get("src"),
                ))

        logger.info("Brave: %s '%s' → %d results", search_type.value, query, len(results))
        return results

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning("Brave rate limited, falling back to DDG")
        else:
            logger.warning("Brave error %s, falling back to DDG", e.response.status_code)
        return None
    except Exception:
        logger.exception("Brave error, falling back to DDG")
        return None


# ═══════════════════════════════════════════════════════════════════════
# ddgs fallback
# ═══════════════════════════════════════════════════════════════════════

_DDG_SAFE_MAP = {
    SafeSearch.STRICT: "on",
    SafeSearch.MODERATE: "moderate",
    SafeSearch.OFF: "off",
}


def _ddg_search(
    query: str,
    search_type: SearchType,
    safe_search: SafeSearch,
    count: int,
) -> list[SearchResult]:
    """ddgs search. Always available, no key needed; safe search is best-effort."""
    ddgs = DDGS()
    ddg_safe = _DDG_SAFE_MAP[safe_search]

    try:
        if search_type == SearchType.WEB:
            raw = ddgs.text(query, safesearch=ddg_safe, max_results=count)
            return [
                SearchResult(title=r.get("title", ""), url=r.get("href", ""), snippet=r.get("body", ""))
                for r in raw
            ]

        elif search_type == SearchType.IMAGE:
            raw = ddgs.images(query, safesearch=ddg_safe, max_results=count)
            return [
                SearchResult(title=r.get("title", ""), url=r.get("image", ""), thumbnail_url=r.get("thumbnail", ""))
                for r in raw
            ]

        elif search_type == SearchType.NEWS:
            raw = ddgs.news(query, safesearch=ddg_safe, max_results=count)
            return [
                SearchResult(title=r.get("title", ""), url=r.get("url", ""), snippet=r.get("body", ""), published=r.get("date", ""))
                for r in raw
            ]

        elif search_type == SearchType.VIDEO:
            raw = ddgs.videos(query, safesearch=ddg_safe, max_results=count)
            return [
                SearchResult(title=r.get("title", ""), url=r.get("content", ""), duration=r.get("duration", ""))
                for r in raw
            ]

    except DDGSException:
        logger.exception("DDG search error")
        raise
    except Exception:
        logger.exception("DDG search error")
        raise

    return []


# ═══════════════════════════════════════════════════════════════════════
# Public API: tries Brave first, falls back to ddgs
# ═══════════════════════════════════════════════════════════════════════

def search(
    query: str,
    search_type: SearchType = SearchType.WEB,
    safe_search: SafeSearch = SafeSearch.MODERATE,
    count: int = 3,
) -> list[SearchResult]:
    """
    Search the web. Tries Brave first (if configured),
    falls back to ddgs.
    """
    count = min(count, 5)

    results = _brave_search(query, search_type, safe_search, count)
    if results is not None:
        return results

    return _ddg_search(query, search_type, safe_search, count)
