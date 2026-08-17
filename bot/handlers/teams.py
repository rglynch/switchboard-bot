"""/teams — random team splitter."""

import random
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from bot.handlers.common import allowed_only


@allowed_only
async def cmd_teams(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    names = ["Player 1", "Player 2", "Player 3"]
    random.shuffle(names)
    n = random.randint(1, 2)
    await update.message.reply_text(
        f"Left: {', '.join(names[:n])}\nRight: {', '.join(names[n:])}"
    )


def register(app) -> None:
    app.add_handler(CommandHandler("teams", cmd_teams))
