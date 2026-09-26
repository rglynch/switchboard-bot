"""
Bot entry point: registers all handlers and starts polling.
"""

import logging
import os

from telegram.ext import ApplicationBuilder

from bot.config import TELEGRAM_BOT_TOKEN, LOG_LEVEL, features_summary
from bot.handlers import help, stocks, search, llm_handler, songlink, gamepass, flip, teams

logging.basicConfig(
    format="%(asctime)s | %(name)-22s | %(levelname)-7s | %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
# This next line is a stopgap measure to prevent API keys from showing in the logs.
# Without it, the bot token and the Finnhub token will be exposed in the logs.
logging.getLogger("httpx").setLevel(logging.WARNING) 
logger = logging.getLogger(__name__)


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set.")

    # Log which features are live
    for feat, enabled in features_summary().items():
        status = "✅" if enabled else "⬜"
        logger.info("  %s %s", status, feat)

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    # Register all handlers (order matters for priority)
    help.register(app)
    stocks.register(app)
    search.register(app)
    llm_handler.register(app)
    gamepass.register(app)
    flip.register(app)
    teams.register(app)
    songlink.register(app)  # group=2, runs after everything else

    logger.info("Bot started, polling for updates …")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
