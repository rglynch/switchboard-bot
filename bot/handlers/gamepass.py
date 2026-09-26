"""
/gp: latest Xbox Game Pass news from the official Xbox Wire RSS feed. No API key needed.
"""

import logging
from xml.etree import ElementTree

import httpx

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from bot.handlers.common import allowed_only, handle_errors

logger = logging.getLogger(__name__)

# Xbox Wire Game Pass category feed
GAMEPASS_RSS_URL = "https://news.xbox.com/en-us/xbox-game-pass/feed/"
# Fallback: general Xbox Wire feed (if the category feed ever moves)
XBOX_WIRE_RSS_URL = "https://news.xbox.com/en-us/feed/"

GP_COUNT = 3


async def _fetch_rss(url: str) -> list[dict]:
    """Fetch and parse an RSS feed, returning items as dicts."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers={"User-Agent": "TelegramBot/1.0"})
        resp.raise_for_status()

    root = ElementTree.fromstring(resp.text)
    items = []

    for item in root.iter("item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub_date = item.findtext("pubDate", "").strip()

        if title and link:
            # pubDate format: "Wed, 19 Mar 2026 17:00:00 +0000"
            date_short = ""
            if pub_date:
                parts = pub_date.split()
                if len(parts) >= 4:
                    date_short = f"{parts[1]} {parts[2]} {parts[3]}"

            items.append({"title": title, "link": link, "date": date_short})

    return items


@allowed_only
@handle_errors
async def cmd_gp(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    status = await update.message.reply_text("🎮 Fetching Game Pass news …")

    items = []
    try:
        items = await _fetch_rss(GAMEPASS_RSS_URL)
    except Exception:
        logger.warning("Game Pass RSS failed, trying general Xbox Wire feed")
        try:
            items = await _fetch_rss(XBOX_WIRE_RSS_URL)
        except Exception:
            logger.exception("Both RSS feeds failed")

    if not items:
        await status.edit_text("Couldn't fetch Game Pass news. Xbox Wire might be down.")
        return

    lines = ["🎮 Xbox Game Pass News\n"]
    for item in items[:GP_COUNT]:
        date_str = f"({item['date']}) " if item["date"] else ""
        lines.append(f"{date_str}{item['link']}")

    await status.edit_text("\n\n".join(lines))


def register(app) -> None:
    app.add_handler(CommandHandler("gp", cmd_gp))
