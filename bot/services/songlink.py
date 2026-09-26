"""Songlink / Odesli API client: resolves music URLs to cross-platform links."""

import logging
from dataclasses import dataclass

import httpx
from bot.config import SONGLINK_API, SONGLINK_API_KEY

logger = logging.getLogger(__name__)


@dataclass
class SonglinkResult:
    page_url: str
    title: str | None = None
    artist: str | None = None


async def resolve(music_url: str) -> SonglinkResult | None:
    """Resolve a music URL to a Songlink universal page. Returns None on failure."""
    params: dict = {"url": music_url, "userCountry": "US"}
    if SONGLINK_API_KEY:
        params["key"] = SONGLINK_API_KEY

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(SONGLINK_API, params=params)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()

        page_url = data.get("pageUrl", "")
        if not page_url:
            return None

        title, artist = None, None
        for entity in data.get("entitiesByUniqueId", {}).values():
            title = title or entity.get("title")
            artist = artist or entity.get("artistName")
            if title and artist:
                break

        return SonglinkResult(page_url=page_url, title=title, artist=artist)
    except Exception:
        logger.exception("Songlink error")
        return None
