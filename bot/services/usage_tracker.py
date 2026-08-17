"""
Usage tracker — monthly request counting with configurable limits
and funny exhaustion messages.
"""

import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

USAGE_FILE = Path("/tmp/bot_usage.json")
WARN_PCT = int(os.getenv("USAGE_WARN_PCT", "80"))

EXHAUSTION_MESSAGES = [
    "🚫 The AI piggy bank is empty. Tell Rick to reload before we can think again.",
    "💀 Brain cells depleted. Pester Rick to feed the meter.",
    "🪫 Out of juice. Rick needs to top up the AI credits or we're stuck being dumb.",
    "🚫 Monthly limit hit. Yell at Rick to refill the balance. Until then, try Google like it's 2005.",
    "💸 We've burned through the budget. Bug Rick to reload or start asking simpler questions.",
    "🧠 The AI ran out of thoughts. Someone tell Rick to Venmo the robots.",
    "☠️ Limit reached. Rick's too cheap to reload the balance. Shame him until he does.",
]


def _get_limits() -> dict[str, int]:
    limits = {}
    for key, val in os.environ.items():
        if key.startswith("MONTHLY_LIMIT_"):
            provider = key.removeprefix("MONTHLY_LIMIT_").lower()
            try:
                limits[provider] = int(val)
            except ValueError:
                logger.warning("Invalid limit for %s: %s", key, val)
    return limits


def _current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def _load() -> dict:
    try:
        if USAGE_FILE.exists():
            data = json.loads(USAGE_FILE.read_text())
            if data.get("month") != _current_month():
                return {"month": _current_month(), "counts": {}}
            return data
    except Exception:
        logger.warning("Could not load usage file, starting fresh")
    return {"month": _current_month(), "counts": {}}


def _save(data: dict) -> None:
    try:
        USAGE_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        logger.warning("Could not save usage file")


def check_limit(provider: str) -> tuple[bool, str | None]:
    """
    Check if a provider is within its monthly limit.
    Returns (allowed, warning_or_block_message).
    """
    limits = _get_limits()

    if provider not in limits:
        return True, None

    data = _load()
    count = data.get("counts", {}).get(provider, 0)
    limit = limits[provider]

    if count >= limit:
        return False, random.choice(EXHAUSTION_MESSAGES)

    warning = None
    pct = (count / limit) * 100
    if pct >= WARN_PCT:
        remaining = limit - count
        warning = f"⚠️ {provider}: {count}/{limit} requests used this month ({remaining} remaining)"

    return True, warning


def record_usage(provider: str) -> None:
    data = _load()
    counts = data.setdefault("counts", {})
    counts[provider] = counts.get(provider, 0) + 1
    _save(data)
    logger.debug("Usage: %s = %d this month", provider, counts[provider])


def get_usage_summary() -> str:
    data = _load()
    limits = _get_limits()
    counts = data.get("counts", {})
    month = data.get("month", _current_month())

    lines = [f"📊 Usage for {month}\n"]

    all_providers = sorted(set(list(limits.keys()) + list(counts.keys())))

    if not all_providers:
        lines.append("No limits configured and no usage recorded.")
        lines.append("Set MONTHLY_LIMIT_CLAUDE=200 (etc.) to enable tracking.")
        return "\n".join(lines)

    for provider in all_providers:
        count = counts.get(provider, 0)
        limit = limits.get(provider)

        if limit:
            pct = (count / limit) * 100
            bar_len = 20
            filled = int(bar_len * min(count, limit) / limit)
            bar = "█" * filled + "░" * (bar_len - filled)
            lines.append(f"  {provider}: {count}/{limit} ({pct:.0f}%)")
            lines.append(f"  [{bar}]")
        else:
            lines.append(f"  {provider}: {count} (no limit set)")

    return "\n".join(lines)
