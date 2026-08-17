"""/start and /help commands."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from bot.handlers.common import allowed_only
from bot.config import MAX_FLIPS

HELP_TEXT = (
    "For the stock bot, use $ followed by a ticker symbol, e.g. $AAPL or $MSFT.\n\n"
    "Stock charts:\n"
    "  - /chart SYMBOL PERIOD INTERVAL — candlestick chart\n"
    "  - /chartv SYMBOL PERIOD INTERVAL — chart with volume\n"
    "  - Add indicators: /chart MSFT 3d 5m rsi macd bb vwap\n"
    "  - /markets — major index overview\n\n"
    "Search:\n"
    "  - /img query — image search\n"
    "  - /web query — web search\n"
    "  - /news query — news search\n"
    "  - /vid query — video search\n"
    "  - Add m for moderate safe search: /imgm query\n"
    "  - Add e to turn safe search off: /imge query\n"
    "  - Add a number for more results (max 5): /imgm4 query\n\n"
    "AI:\n"
    "  - /ask question — ask the default AI\n"
    "  - /ask:provider question — pick a provider (e.g. /ask:claude)\n"
    "  - /ask:provider:model question — pick a specific model\n"
    "  - /ask:web question — include web search (Grok only, extra cost)\n"
    "  - /search query — web-grounded AI search (Perplexity)\n"
    "  - /models — see available providers and models\n"
    "  - /usage — check monthly usage and limits\n\n"
    "You may use the command /gp to see the latest three Xbox Game Pass news results.\n\n"
    "Sharing a song link to a song, music, or playlist on a music service such as "
    "Spotify, YouTube Music, etc. will return a Songlink which contains a link to "
    "all supported music services.\n\n"
    f"Lastly, you can use /flip or /flip n, where n is an integer (maximum {MAX_FLIPS}), "
    "to flip a coin 1 or n times, respectively."
)


@allowed_only
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Let's go!")


@allowed_only
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)


def register(app) -> None:
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
