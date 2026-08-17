"""
Search commands — provider-agnostic, backed by DuckDuckGo.

Commands:
    /img query        → image search (strict safe search)
    /imgm query       → image search (moderate)
    /imge query       → image search (safe search off)
    /imge4 query      → 4 images, safe search off

    /web, /webm, /webe  → web search
    /news, /newsm       → news search
    /vid, /vidm         → video search

Suffix grammar:
    m = moderate safe search
    e = safe search off
    trailing digit = number of results (1-5)
    no suffix = strict safe search, 1 result
"""

import re
import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.handlers.common import allowed_only, handle_errors
from bot.services.search import SearchType, SafeSearch, search, SearchResult

logger = logging.getLogger(__name__)

MAX_RESULTS = 5
DEFAULT_RESULTS = 1

# Map command base → search type
_CMD_MAP = {
    "img":  SearchType.IMAGE,
    "web":  SearchType.WEB,
    "news": SearchType.NEWS,
    "vid":  SearchType.VIDEO,
}


def _parse_command(command: str) -> tuple[SearchType, SafeSearch, int] | None:
    """
    Parse /img, /imgm4, /webe, /news3, etc.
    Returns (search_type, safe_search, count) or None if not a valid command.
    """
    cmd = command.lower().lstrip("/")

    # Match: (img|web|news|vid) + optional (m|e) + optional (digit)
    match = re.match(r"^(img|web|news|vid)(m|e)?(\d)?$", cmd)
    if not match:
        return None

    base, safe_char, count_char = match.groups()

    search_type = _CMD_MAP[base]

    if safe_char == "e":
        safe = SafeSearch.OFF
    elif safe_char == "m":
        safe = SafeSearch.MODERATE
    else:
        safe = SafeSearch.STRICT

    count = int(count_char) if count_char else DEFAULT_RESULTS
    count = min(count, MAX_RESULTS)

    # DDG video search doesn't reliably support safe search off
    if search_type == SearchType.VIDEO and safe == SafeSearch.OFF:
        safe = SafeSearch.MODERATE

    return search_type, safe, count


@allowed_only
@handle_errors
async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all /img, /web, /news, /vid commands."""
    full_text = update.message.text or ""
    parts = full_text.split(None, 1)

    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(
            "Usage: /img query, /web query, /news query, /vid query\n"
            "Add m for moderate, e for safe search off: /imge query\n"
            "Add a number for more results: /imgm4 query\n"
            "See /help for full details."
        )
        return

    command_part = parts[0].lstrip("/")
    query = parts[1].strip()

    parsed = _parse_command(command_part)
    if parsed is None:
        await update.message.reply_text("Unknown search command. Try /img, /web, /news, or /vid.")
        return

    search_type, safe, count = parsed

    try:
        results = search(query, search_type, safe, count)

        if not results:
            await update.message.reply_text(f"No {search_type.value} results found.")
            return

        for r in results:
            if search_type == SearchType.IMAGE:
                try:
                    await update.message.reply_photo(
                        photo=r.url,
                        caption=r.title[:200] if r.title else None,
                    )
                except Exception:
                    # Fallback to link if photo send fails
                    await update.message.reply_text(r.url)

            elif search_type == SearchType.WEB:
                await update.message.reply_text(r.url)

            elif search_type == SearchType.NEWS:
                await update.message.reply_text(r.url)

            elif search_type == SearchType.VIDEO:
                await update.message.reply_text(r.url)

    except Exception:
        logger.exception("Search error for %s (%s)", query, search_type)
        await update.message.reply_text(
            f"Oh dang, there's an error with {search_type.value} search."
        )


def register(app) -> None:
    # Catch all /img*, /web*, /news*, /vid* commands
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^/(img|web|news|vid)"),
        cmd_search,
    ))
