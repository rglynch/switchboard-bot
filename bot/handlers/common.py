"""Shared handler decorators."""

import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import get_allowed_chat_ids

logger = logging.getLogger(__name__)
_ALLOWED = get_allowed_chat_ids()


def allowed_only(func):
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *a, **kw):
        if _ALLOWED is not None and update.effective_chat.id not in _ALLOWED:
            logger.info("Update received from unauthorized chat: %s", update.effective_chat.id)
            return
        return await func(update, ctx, *a, **kw)
    return wrapper


def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *a, **kw):
        try:
            return await func(update, ctx, *a, **kw)
        except Exception:
            logger.exception("Unhandled error in %s", func.__name__)
            if update.message:
                await update.message.reply_text("💥 Something went wrong. Try again later.")
    return wrapper
