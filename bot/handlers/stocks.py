"""
Stock commands:
  - $SYMBOL inline detection for quick quotes
  - /chart and /chartv for candlestick charts with optional indicators
  - /markets for index overview
  - Easter eggs (trigger on plain text, no $ required)
"""

import logging
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from bot.handlers.common import allowed_only, handle_errors
from bot.services.stock_data import (
    TickerNotFoundError, InvalidParameterError,
    fetch_quote, fetch_chart_data, fetch_indices, parse_symbols,
)
from bot.services.chart_renderer import render, VALID_INDICATORS

logger = logging.getLogger(__name__)


# ── Easter eggs (fires on ALL text, no $ needed) ─────────────────────

@allowed_only
@handle_errors
async def on_easter_eggs(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Check every text message for easter egg triggers."""
    text = update.message.text or ""

    # Skip commands
    if text.strip().startswith("/"):
        return

    text_lower = text.lower()

    # ── APPL typo (works with or without $) ──────────────────────
    if "appl" in text_lower and "apple" not in text_lower:
        # Only trigger if they wrote "appl" as a stock-like reference
        # Match: $appl, appl, APPL, but not "apple", "application", etc.
        if re.search(r"(?:^|\s|\$)appl(?:\s|$|[^a-zA-Z])", text_lower):
            try:
                q = fetch_quote("AAPL")
                sign = "+" if q.change >= 0 else ""
                await update.message.reply_text(
                    f"You probably meant $AAPL.\n\n"
                    f"{q.company_name} ({q.symbol}) | ${q.price} | "
                    f"{sign}{q.change_pct}% | {sign}${q.change}"
                )
            except Exception:
                await update.message.reply_text("You probably meant $AAPL.")
            return


# ── $SYMBOL inline detection ─────────────────────────────────────────

@allowed_only
@handle_errors
async def on_dollar_symbol(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Detect $SYMBOL mentions and reply with quotes."""
    text = update.message.text or ""

    # Skip commands
    if text.strip().startswith("/"):
        return

    text_lower = text.lower()

    # Skip if an easter egg already handled this message
    if re.search(r"(?:^|\s|\$)appl(?:\s|$|[^a-zA-Z])", text_lower) and "apple" not in text_lower:
        return

    # Normal $SYMBOL quotes
    symbols = parse_symbols(text)
    for symbol in symbols:
        try:
            q = fetch_quote(symbol)
            if q.change_pct > 0:
                direction = "is up!"
                sign = "+"
            elif q.change_pct < 0:
                direction = "is down!"
                sign = ""
            else:
                await update.message.reply_text(
                    f"{q.company_name} ({q.symbol}), the stock hasn't shown any movement today"
                )
                continue

            await update.message.reply_text(
                f"{q.company_name} ({q.symbol}) {direction} | "
                f"${q.price} | {sign}{q.change_pct}% | {sign}${q.change}"
            )
        except TickerNotFoundError:
            pass  # Silently skip unknown symbols
        except Exception:
            logger.exception("Quote error for %s", symbol)


# ── /chart and /chartv ───────────────────────────────────────────────

@allowed_only
@handle_errors
async def cmd_chart(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /chart SYMBOL PERIOD INTERVAL [indicators...]
    /chartv SYMBOL PERIOD INTERVAL [indicators...]

    Examples:
        /chart MSFT 3d 1m
        /chart AAPL 1y 1d rsi macd bb
    """
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "Usage: /chart SYMBOL PERIOD INTERVAL [rsi] [macd] [bb] [vwap]\n"
            "Example: /chart MSFT 3d 1m rsi macd"
        )
        return

    symbol = args[0].replace("$", "")

    if len(args) == 1:
        period, interval = "1y", "1d"
    elif len(args) == 2:
        period = args[1]
        from bot.config import PERIODS
        _, approx_days = PERIODS.get(period.lower(), ("", 999))
        interval = "30m" if approx_days <= 5 else "1d"
    else:
        period, interval = args[1], args[2]

    indicators = [a.lower() for a in args[3:] if a.lower() in VALID_INDICATORS]

    status = await update.message.reply_text(f"⏳ Fetching {symbol.upper()} …")

    try:
        md = fetch_chart_data(symbol, period, interval)
        buf = render(md, indicators=indicators)

        indicator_str = f" + {', '.join(i.upper() for i in indicators)}" if indicators else ""
        await update.message.reply_photo(
            photo=buf,
            caption=(
                f"{md.symbol} ({md.company_name})\n"
                f"{md.interval_label} candles · {md.period_label} period{indicator_str}"
            ),
        )
        await status.delete()

    except TickerNotFoundError as e:
        await status.edit_text(f"❌ {e}")
    except InvalidParameterError as e:
        await status.edit_text(f"⚠️ {e}")


# ── /markets ─────────────────────────────────────────────────────────

@allowed_only
@handle_errors
async def cmd_markets(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    status = await update.message.reply_text("⏳ Fetching markets …")
    data = fetch_indices()
    lines = ["🌎 Market Overview\n"]
    for name, info in data.items():
        if info is None:
            lines.append(f"  {name}: unavailable")
            continue
        icon = "🟢" if info["change"] >= 0 else "🔴"
        sign = "+" if info["change"] >= 0 else ""
        lines.append(f"{icon} {name}: {info['last']:,.2f}  ({sign}{info['pct']:.2f}%)")
    await status.edit_text("\n".join(lines))


# ── Register ─────────────────────────────────────────────────────────

def register(app) -> None:
    app.add_handler(CommandHandler("chart", cmd_chart))
    app.add_handler(CommandHandler("chartv", cmd_chart))
    app.add_handler(CommandHandler("markets", cmd_markets))

    # Easter eggs fire on ALL text messages (no $ required), group 1
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, on_easter_eggs),
        group=1,
    )

    # $SYMBOL detection only fires on messages containing $, group 2
    # Runs after easter eggs so it can skip already-handled messages
    app.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"\$[a-zA-Z]"), on_dollar_symbol),
        group=2,
    )
