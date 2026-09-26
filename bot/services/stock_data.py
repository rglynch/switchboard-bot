"""
Market data retrieval.

Strategy:
  - Quick quotes ($SYMBOL): Finnhub first (real-time), yfinance fallback
  - Chart data (OHLCV: open, high, low, close, volume): always yfinance
  - Market indices: always yfinance
Finnhub is used only for real-time quotes.

If FINNHUB_API_KEY is not set, everything falls back to yfinance silently.
"""

import logging
import os
import re
from dataclasses import dataclass

import httpx
import pandas as pd
import yfinance as yf

from bot.config import INTERVALS, PERIODS

logger = logging.getLogger(__name__)

FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE: str = "https://finnhub.io/api/v1"


class TickerNotFoundError(Exception):
    pass

class InvalidParameterError(Exception):
    pass


@dataclass
class MarketData:
    df: pd.DataFrame
    symbol: str
    company_name: str
    period_label: str
    interval_label: str
    currency: str


@dataclass
class QuoteData:
    symbol: str
    company_name: str
    price: float
    change: float
    change_pct: float
    currency: str
    source: str  # "finnhub" or "yfinance"


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def parse_symbols(text: str) -> list[str]:
    """Extract $SYMBOL mentions from a message."""
    return list(set(re.findall(r"\$([a-zA-Z]{1,5})", text)))


def validate_chart_params(period: str, interval: str) -> tuple[str, str]:
    period_l, interval_l = period.lower(), interval.lower()

    if interval_l not in INTERVALS:
        raise InvalidParameterError(
            f"Invalid interval `{interval}`.\n"
            f"Valid: {', '.join(sorted(INTERVALS.keys()))}"
        )
    if period_l not in PERIODS:
        raise InvalidParameterError(
            f"Invalid period `{period}`.\n"
            f"Valid: {', '.join(sorted(PERIODS.keys()))}"
        )

    yf_period, approx_days = PERIODS[period_l]
    spec = INTERVALS[interval_l]

    if approx_days > spec.max_period_days:
        raise InvalidParameterError(
            f"Intraday data cannot extend past ~{spec.max_period_days} days.\n"
            f"Try a shorter period or wider interval."
        )
    return yf_period, spec.yf_key


def _get_ticker_meta(symbol: str) -> tuple[str, str]:
    """Resolve company name + currency via yfinance, with fallback."""
    try:
        info = yf.Ticker(symbol.upper()).info or {}
        name = info.get("shortName") or info.get("longName") or symbol.upper()
        return name, info.get("currency", "USD")
    except Exception:
        return symbol.upper(), "USD"


# ═══════════════════════════════════════════════════════════════════════
# Finnhub quote (real-time US stocks)
# ═══════════════════════════════════════════════════════════════════════

def _finnhub_quote(symbol: str) -> QuoteData | None:
    """
    Try to get a real-time quote from Finnhub.
    Returns None if Finnhub is unavailable or the symbol isn't found.
    """
    if not FINNHUB_API_KEY:
        return None

    try:
        # Quote endpoint
        resp = httpx.get(
            f"{FINNHUB_BASE}/quote",
            params={"symbol": symbol.upper(), "token": FINNHUB_API_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        q = resp.json()

        # Finnhub returns c=0 for unknown symbols
        if not q.get("c") or q["c"] == 0:
            return None

        # Company profile for the name
        name = symbol.upper()
        try:
            resp2 = httpx.get(
                f"{FINNHUB_BASE}/stock/profile2",
                params={"symbol": symbol.upper(), "token": FINNHUB_API_KEY},
                timeout=10,
            )
            if resp2.status_code == 200:
                profile = resp2.json()
                name = profile.get("name") or symbol.upper()
        except Exception:
            pass

        price = round(q["c"], 2)
        change = round(q["d"], 2) if q.get("d") is not None else 0
        change_pct = round(q["dp"], 2) if q.get("dp") is not None else 0

        return QuoteData(
            symbol=symbol.upper(),
            company_name=name,
            price=price,
            change=change,
            change_pct=change_pct,
            currency="USD",
            source="finnhub",
        )

    except Exception:
        logger.debug("Finnhub quote failed for %s, will fall back to yfinance", symbol)
        return None


# ═══════════════════════════════════════════════════════════════════════
# yfinance quote (fallback: delayed, but covers everything)
# ═══════════════════════════════════════════════════════════════════════

def _yfinance_quote(symbol: str) -> QuoteData:
    """Get a quote from yfinance. Raises TickerNotFoundError on failure."""
    hist = yf.Ticker(symbol.upper()).history(period="2d")
    if hist.empty:
        raise TickerNotFoundError(f"`{symbol.upper()}` not found or no data.")

    name, currency = _get_ticker_meta(symbol)
    last = hist["Close"].iloc[-1]
    prev = hist["Close"].iloc[-2] if len(hist) > 1 else hist["Open"].iloc[-1]
    chg = last - prev
    pct = (chg / prev) * 100 if prev else 0

    return QuoteData(
        symbol=symbol.upper(),
        company_name=name,
        price=round(last, 2),
        change=round(chg, 2),
        change_pct=round(pct, 2),
        currency=currency,
        source="yfinance",
    )


# ═══════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════

def fetch_quote(symbol: str) -> QuoteData:
    """
    Fetch a stock quote. Tries Finnhub first (real-time),
    falls back to yfinance (delayed but covers everything).
    """
    # Try Finnhub first for real-time US quotes
    result = _finnhub_quote(symbol)
    if result:
        logger.info("Quote for %s via Finnhub (real-time)", symbol.upper())
        return result

    # Fall back to yfinance
    logger.info("Quote for %s via yfinance (fallback)", symbol.upper())
    return _yfinance_quote(symbol)


def fetch_chart_data(symbol: str, period: str, interval: str) -> MarketData:
    """Fetch OHLCV data for chart rendering (always yfinance)."""
    yf_period, yf_interval = validate_chart_params(period, interval)
    name, currency = _get_ticker_meta(symbol)

    logger.info("Chart data for %s period=%s interval=%s via yfinance", symbol.upper(), yf_period, yf_interval)
    df = yf.Ticker(symbol.upper()).history(period=yf_period, interval=yf_interval)

    if df.empty:
        raise TickerNotFoundError(
            f"No data for `{symbol.upper()}`.\nCheck the symbol or try different params."
        )
    df.columns = [c.title() for c in df.columns]

    return MarketData(
        df=df, symbol=symbol.upper(), company_name=name,
        period_label=period.upper(),
        interval_label=INTERVALS[interval.lower()].label,
        currency=currency,
    )


def fetch_indices() -> dict[str, dict | None]:
    """Current values for major market indices (always yfinance, which handles ^ symbols)."""
    indices = {
        "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow": "^DJI",
        "Russell": "^RUT", "VIX": "^VIX", "10Y Yield": "^TNX",
    }
    results = {}
    for name, sym in indices.items():
        try:
            hist = yf.Ticker(sym).history(period="2d")
            if hist.empty or len(hist) < 2:
                results[name] = None
                continue
            prev, last = hist["Close"].iloc[-2], hist["Close"].iloc[-1]
            chg = last - prev
            results[name] = {"last": last, "change": chg, "pct": (chg / prev) * 100}
        except Exception:
            results[name] = None
    return results
