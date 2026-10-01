"""
Central configuration for the bot: most environment variables and shared constants.
Search, market data and usage limits read their own settings in their modules.
"""

import os
import logging
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Core
# ═══════════════════════════════════════════════════════════════════════

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


def get_allowed_chat_ids() -> set[int] | None:
    raw = os.getenv("ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        logger.warning("ALLOWED_CHAT_IDS is not set, allowing all chats (dangerous)!")
        return None
    try:
        chat_ids = {int(cid.strip()) for cid in raw.split(",") if cid.strip()}
        logger.info("ALLOWED_CHAT_IDS is set, restricting access to: %s", chat_ids)
        return chat_ids
    except ValueError:
        logger.warning("Invalid ALLOWED_CHAT_IDS, ignoring allowlist (dangerous)!")
        return None


# ═══════════════════════════════════════════════════════════════════════
# Search (Brave Search API with a key, keyless ddgs fallback)
# ═══════════════════════════════════════════════════════════════════════

SEARCH_MAX_RESULTS: int = 5


# ═══════════════════════════════════════════════════════════════════════
# LLM Providers
# ═══════════════════════════════════════════════════════════════════════

LLM_DEFAULT_PROVIDER: str = os.getenv("LLM_DEFAULT", "grok")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL: str = os.getenv("PERPLEXITY_MODEL", "sonar")

GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
GROK_MODEL: str = os.getenv("GROK_MODEL", "grok-4.1-fast")


# ═══════════════════════════════════════════════════════════════════════
# Model restrictions (per-provider)
# If set, only these shortcuts/model strings are allowed.
# Comma-separated. Supports both shortcuts and full model strings.
# e.g. ALLOWED_MODELS_CLAUDE=haiku
# e.g. ALLOWED_MODELS_CLAUDE=haiku,claude-sonnet-4-6
# If not set, all models for that provider are available.
# ═══════════════════════════════════════════════════════════════════════

def get_allowed_models(provider: str) -> set[str] | None:
    """Get allowed models for a provider. Returns None if unrestricted."""
    raw = os.getenv(f"ALLOWED_MODELS_{provider.upper()}", "").strip()
    if not raw:
        return None
    return {m.strip().lower() for m in raw.split(",") if m.strip()}


# ═══════════════════════════════════════════════════════════════════════
# Stock Charts
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class IntervalSpec:
    yf_key: str
    max_period_days: int
    label: str


INTERVALS: dict[str, IntervalSpec] = {
    "1m":  IntervalSpec("1m",  7,    "1 Minute"),
    "2m":  IntervalSpec("2m",  60,   "2 Minute"),
    "5m":  IntervalSpec("5m",  60,   "5 Minute"),
    "15m": IntervalSpec("15m", 60,   "15 Minute"),
    "30m": IntervalSpec("30m", 60,   "30 Minute"),
    "60m": IntervalSpec("60m", 60,   "60 Minute"),
    "90m": IntervalSpec("90m", 60,   "90 Minute"),
    "1h":  IntervalSpec("1h",  730,  "1 Hour"),
    "1d":  IntervalSpec("1d",  3650, "Daily"),
    "5d":  IntervalSpec("5d",  3650, "5 Day"),
    "1wk": IntervalSpec("1wk", 3650, "Weekly"),
    "1mo": IntervalSpec("1mo", 3650, "Monthly"),
}

PERIODS: dict[str, tuple[str, int]] = {
    "1d":  ("1d",   1),    "2d":  ("2d",   2),    "3d":  ("3d",   3),
    "5d":  ("5d",   5),    "1w":  ("5d",   5),    "2w":  ("10d",  10),
    "1mo": ("1mo",  30),   "3mo": ("3mo",  90),   "6mo": ("6mo",  180),
    "1y":  ("1y",   365),  "2y":  ("2y",   730),  "5y":  ("5y",   1825),
    "10y": ("10y",  3650), "ytd": ("ytd",  365),  "max": ("max",  3650),
}

CHART_STYLE: dict = {
    "figsize": (14, 8), "dpi": 150,
    "up_color": "#26a69a", "down_color": "#ef5350",
    "bg_color": "#131722", "face_color": "#131722",
    "grid_color": "#1e222d", "text_color": "#d1d4dc",
    "ma_colors": ["#f5c842", "#2196f3", "#e91e63"],
}


# ═══════════════════════════════════════════════════════════════════════
# Songlink
# ═══════════════════════════════════════════════════════════════════════

SONGLINK_API: str = "https://api.song.link/v1-alpha.1/links"
SONGLINK_API_KEY: str = os.getenv("SONGLINK_API_KEY", "")

MUSIC_DOMAINS: list[str] = [
    "music.amazon.com", "deezer.com", "geo.music.apple.com",
    "music.apple.com", "napster.com", "pandora.app.link",
    "open.spotify.com", "listen.tidal.com", "tidal.com",
    "music.yandex.ru", "music.youtube.com", "soundcloud.com",
]


# ═══════════════════════════════════════════════════════════════════════
# Misc
# ═══════════════════════════════════════════════════════════════════════

MAX_FLIPS: int = 10


# ═══════════════════════════════════════════════════════════════════════
# Feature flags
# ═══════════════════════════════════════════════════════════════════════

def features_summary() -> dict[str, bool]:
    return {
        "search_brave":   bool(os.getenv("BRAVE_API_KEY")),
        "search_ddg":     True,   # always available as fallback
        "llm_claude":     bool(ANTHROPIC_API_KEY),
        "llm_gpt":        bool(OPENAI_API_KEY),
        "llm_perplexity": bool(PERPLEXITY_API_KEY),
        "llm_grok":       bool(GROK_API_KEY),
        "stock_realtime": bool(os.getenv("FINNHUB_API_KEY")),
        "stock_chart":    True,
        "stock_quote":    True,
        "songlink":       True,
        "gamepass":       True,
        "flip":           True,
    }
