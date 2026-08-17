"""/flip — flip a coin 1 or N times."""

import random
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from bot.handlers.common import allowed_only
from bot.config import MAX_FLIPS


@allowed_only
async def cmd_flip(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    n = 1
    if ctx.args:
        try:
            n = max(1, min(int(ctx.args[0]), MAX_FLIPS))
        except ValueError:
            await update.message.reply_text(f"Usage: /flip or /flip N (max {MAX_FLIPS})")
            return

    flips = [random.choice(("H", "T")) for _ in range(n)]

    if n == 1:
        await update.message.reply_text(f"🪙 {flips[0]}")
    else:
        lines = [f"Flip {i+1}: \t{f}" for i, f in enumerate(flips)]
        h, t = flips.count("H"), flips.count("T")
        lines.append(f"\nHeads: {h} | Tails: {t}")
        await update.message.reply_text("\n".join(lines))


def register(app) -> None:
    app.add_handler(CommandHandler("flip", cmd_flip))
