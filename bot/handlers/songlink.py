"""Auto-detect music URLs in messages and reply with Songlink."""

import re
import logging
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import MUSIC_DOMAINS
from bot.handlers.common import allowed_only
from bot.services.songlink import resolve

logger = logging.getLogger(__name__)
_URL_RE = re.compile(r"https?://[^\s<>\"']+")


def _is_music_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return any(d in host for d in MUSIC_DOMAINS)
    except Exception:
        return False


@allowed_only
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or update.message.caption or ""
    urls = _URL_RE.findall(text)
    music_urls = [u for u in urls if _is_music_url(u)]

    if not music_urls:
        return

    result = await resolve(music_urls[0])
    if result is None:
        return

    label = ""
    if result.title and result.artist:
        label = f"🎵 {result.title} by {result.artist}\n"
    elif result.title:
        label = f"🎵 {result.title}\n"

    await update.message.reply_text(f"{label}🔗 {result.page_url}")


def register(app) -> None:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message), group=3)
