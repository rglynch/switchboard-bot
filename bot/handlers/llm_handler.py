"""
/ask, /search, /models, and /usage commands.

Syntax:
    /ask question                   → default provider, default model
    /ask:claude question            → Claude, default Claude model
    /ask:claude:haiku question      → Claude, Haiku model
    /ask:grok:fast question         → Grok, grok-4-1-fast
    /search query                   → always Perplexity Sonar
    /search:pro query               → Perplexity Sonar Pro
    /models                         → show available providers and allowed models
    /usage                          → show monthly usage and limits
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, filters

from bot.handlers.common import allowed_only, handle_errors
from bot.services.llm import registry
from bot.services.llm_providers.base import ModelNotAllowedError
from bot.services.usage_tracker import check_limit, record_usage, get_usage_summary

logger = logging.getLogger(__name__)


def _parse_ask_command(command_text: str) -> tuple[str | None, str | None]:
    """
    Parse /ask command for provider, model, and web search flag.
    /ask                  → (None, None, False)
    /ask:claude           → ("claude", None, False)
    /ask:claude:haiku     → ("claude", "haiku", False)
    /ask:grok:web         → ("grok", None, True)
    /ask:grok:fast:web    → ("grok", "fast", True)
    """
    parts = command_text.lstrip("/").split(":")

    # Check for :web flag anywhere and remove it
    web_search = "web" in parts[1:]
    parts = [p for p in parts if p != "web"]

    provider = parts[1] if len(parts) > 1 and parts[1] else None
    model = parts[2] if len(parts) > 2 and parts[2] else None
    return provider, model, web_search


@allowed_only
@handle_errors
async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    full_text = update.message.text or ""
    parts = full_text.split(None, 1)

    if len(parts) < 2 or not parts[1].strip():
        avail = ", ".join(registry.available) or "none configured"
        await update.message.reply_text(
            f"Usage:\n"
            f"  /ask question\n"
            f"  /ask:provider question\n"
            f"  /ask:provider:model question\n\n"
            f"Providers: {avail} (default: {registry.default_name})\n"
            f"Use /models to see what's available."
        )
        return

    command = parts[0]
    question = parts[1].strip()
    provider, model, web_search = _parse_ask_command(command)

    resolved_provider = provider or registry.default_name

    # Check usage limit
    allowed, warning = check_limit(resolved_provider)
    if not allowed:
        await update.message.reply_text(warning)
        return

    status = await update.message.reply_text("🔍 Searching …" if web_search else "🤔 Thinking …")

    try:
        response, used_provider, used_model = await registry.chat(
            question, provider=provider, model=model, web_search=web_search,
        )

        record_usage(used_provider)

        if len(response) > 4000:
            response = response[:4000] + "\n\n_(truncated)_"

        model_short = used_model.split("/")[-1]
        web_tag = ":web" if web_search else ""
        footer = f"[{used_provider}:{model_short}{web_tag}]"
        if warning:
            footer += f"\n{warning}"

        await status.edit_text(f"{response}\n\n{footer}")

    except ModelNotAllowedError as e:
        await status.edit_text(f"⚠️ {e}")
    except RuntimeError as e:
        await status.edit_text(f"⚠️ {e}")


@allowed_only
@handle_errors
async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Always routes to Perplexity for web-grounded answers."""
    full_text = update.message.text or ""
    parts = full_text.split(None, 1)

    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text("Usage: /search your query here")
        return

    command = parts[0]
    query = parts[1].strip()
    _, model, _ = _parse_ask_command(command.replace("search", "ask", 1))

    allowed, warning = check_limit("perplexity")
    if not allowed:
        await update.message.reply_text(warning)
        return

    status = await update.message.reply_text("🔍 Searching …")

    try:
        response, _, used_model = await registry.chat(
            query, provider="perplexity", model=model,
        )

        record_usage("perplexity")

        if len(response) > 4000:
            response = response[:4000] + "\n\n_(truncated)_"

        text = response
        if warning:
            text += f"\n\n{warning}"

        await status.edit_text(text)

    except ModelNotAllowedError as e:
        await status.edit_text(f"⚠️ {e}")
    except RuntimeError as e:
        await status.edit_text(f"⚠️ {e}")


@allowed_only
async def cmd_models(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available providers and their allowed models."""
    header = "🤖 Available providers and models:\n\n"
    await update.message.reply_text(header + registry.help_text())


@allowed_only
async def cmd_usage(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show monthly usage stats and limits."""
    await update.message.reply_text(get_usage_summary())


def register(app) -> None:
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/ask"), cmd_ask))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/search\b"), cmd_search))
    app.add_handler(CommandHandler("models", cmd_models))
    app.add_handler(CommandHandler("usage", cmd_usage))