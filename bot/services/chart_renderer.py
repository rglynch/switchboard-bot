"""
Candlestick chart rendering with a TradingView-inspired dark theme.

Supports optional indicators: rsi, macd, bb (Bollinger Bands), vwap.
Usage: render(market_data, indicators=["rsi", "bb"])
"""

import io
import logging
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd

from bot.config import CHART_STYLE
from bot.services.stock_data import MarketData

logger = logging.getLogger(__name__)

# ── Custom mpf style ─────────────────────────────────────────────────
_MC = mpf.make_marketcolors(
    up=CHART_STYLE["up_color"], down=CHART_STYLE["down_color"],
    wick={"up": CHART_STYLE["up_color"], "down": CHART_STYLE["down_color"]},
    edge={"up": CHART_STYLE["up_color"], "down": CHART_STYLE["down_color"]},
    volume={"up": CHART_STYLE["up_color"], "down": CHART_STYLE["down_color"]},
)

MPF_STYLE = mpf.make_mpf_style(
    marketcolors=_MC,
    facecolor=CHART_STYLE["face_color"],
    figcolor=CHART_STYLE["bg_color"],
    gridcolor=CHART_STYLE["grid_color"],
    gridstyle="--", gridaxis="both", y_on_right=True,
    rc={
        "axes.labelcolor": CHART_STYLE["text_color"],
        "xtick.color": CHART_STYLE["text_color"],
        "ytick.color": CHART_STYLE["text_color"],
        "font.size": 9,
    },
)

VALID_INDICATORS = {"rsi", "macd", "bb", "vwap"}


# ── Indicator calculations ───────────────────────────────────────────

def _calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _calc_macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal
    return macd_line, signal, histogram


def _calc_bollinger(close: pd.Series, period: int = 20) -> tuple[pd.Series, pd.Series, pd.Series]:
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    return sma + 2 * std, sma, sma - 2 * std


def _calc_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()


# ── EMA overlays ─────────────────────────────────────────────────────

def _ema_plots(df: pd.DataFrame) -> list:
    colors = CHART_STYLE["ma_colors"]
    plots = []
    for p, c in zip([9, 21, 55], colors):
        if len(df) >= p:
            ema = df["Close"].ewm(span=p, adjust=False).mean()
            plots.append(mpf.make_addplot(ema, color=c, width=1.0))
    return plots


# ── Subtitle ─────────────────────────────────────────────────────────

def _subtitle(md: MarketData) -> str:
    last = md.df.iloc[-1]
    prev = md.df["Close"].iloc[-2] if len(md.df) > 1 else last["Open"]
    chg = last["Close"] - prev
    pct = (chg / prev) * 100 if prev else 0
    arrow, sign = ("▲", "+") if chg >= 0 else ("▼", "")
    return (
        f"{md.company_name}  •  {md.interval_label} candles  •  {md.period_label} period\n"
        f"Last: {last['Close']:.2f} {md.currency}  "
        f"{arrow} {sign}{chg:.2f} ({sign}{pct:.2f}%)  •  "
        f"Vol: {int(last.get('Volume', 0)):,}"
    )


# ── Main render function ─────────────────────────────────────────────

def render(md: MarketData, indicators: list[str] | None = None) -> io.BytesIO:
    """
    Render candlestick chart to in-memory PNG.

    indicators: optional list of "rsi", "macd", "bb", "vwap"
    """
    indicators = [i.lower() for i in (indicators or []) if i.lower() in VALID_INDICATORS]
    df = md.df.copy()

    add_plots = _ema_plots(df)

    # Bollinger Bands overlay on price panel
    if "bb" in indicators and len(df) >= 20:
        upper, mid, lower = _calc_bollinger(df["Close"])
        add_plots.append(mpf.make_addplot(upper, color="#787b86", width=0.7, linestyle="--"))
        add_plots.append(mpf.make_addplot(mid, color="#787b86", width=0.5, linestyle=":"))
        add_plots.append(mpf.make_addplot(lower, color="#787b86", width=0.7, linestyle="--"))

    # VWAP overlay on price panel
    if "vwap" in indicators and "Volume" in df.columns:
        vwap = _calc_vwap(df)
        add_plots.append(mpf.make_addplot(vwap, color="#ff9800", width=1.2, linestyle="-"))

    # Count sub-panels needed (volume is always panel 1)
    extra_panels = []
    if "rsi" in indicators and len(df) >= 14:
        extra_panels.append("rsi")
    if "macd" in indicators and len(df) >= 26:
        extra_panels.append("macd")

    # RSI panel
    if "rsi" in extra_panels:
        rsi = _calc_rsi(df["Close"])
        add_plots.append(mpf.make_addplot(rsi, panel=2, color="#ab47bc", width=1.0, ylabel="RSI"))
        # Overbought/oversold reference lines
        add_plots.append(mpf.make_addplot(
            pd.Series(70, index=df.index), panel=2, color="#ef5350",
            width=0.5, linestyle="--", secondary_y=False,
        ))
        add_plots.append(mpf.make_addplot(
            pd.Series(30, index=df.index), panel=2, color="#26a69a",
            width=0.5, linestyle="--", secondary_y=False,
        ))

    # MACD panel
    if "macd" in extra_panels:
        macd_panel = 3 if "rsi" in extra_panels else 2
        macd_line, signal, hist = _calc_macd(df["Close"])
        add_plots.append(mpf.make_addplot(macd_line, panel=macd_panel, color="#2196f3", width=1.0, ylabel="MACD"))
        add_plots.append(mpf.make_addplot(signal, panel=macd_panel, color="#ff9800", width=1.0))
        # Histogram as bar chart
        colors = ["#26a69a" if v >= 0 else "#ef5350" for v in hist]
        add_plots.append(mpf.make_addplot(hist, panel=macd_panel, type="bar", color=colors, width=0.7))

    # Figure sizing
    n_panels = 2 + len(extra_panels)  # price + volume + extras
    panel_ratios = [6, 2] + [2] * len(extra_panels)
    fig_h = 8 + 2 * len(extra_panels)

    is_intraday = any(k in md.interval_label.lower() for k in ("minute", "hour"))
    dt_fmt = "%b %d %H:%M" if is_intraday else "%b %d '%y"

    fig, axes = mpf.plot(
        df, type="candle", style=MPF_STYLE, volume=True,
        addplot=add_plots if add_plots else None,
        figsize=(14, fig_h), returnfig=True, tight_layout=True,
        datetime_format=dt_fmt, warn_too_much_data=99999,
        panel_ratios=panel_ratios,
    )

    # Title + subtitle
    tc = CHART_STYLE["text_color"]
    fig.suptitle(md.symbol, x=0.06, y=0.97, fontsize=18, fontweight="bold", color=tc, ha="left")
    fig.text(0.06, 0.935, _subtitle(md), fontsize=9, color="#808a9d", ha="left")

    # EMA legend
    for i, (p, c) in enumerate(zip([9, 21, 55], CHART_STYLE["ma_colors"])):
        if len(df) >= p:
            val = df["Close"].ewm(span=p, adjust=False).mean().iloc[-1]
            axes[0].text(
                0.98, 0.98 - i * 0.04, f"EMA{p}: {val:.2f}",
                transform=axes[0].transAxes, fontsize=8, color=c, ha="right", va="top",
            )

    # Indicator labels
    indicator_labels = []
    if "bb" in indicators:
        indicator_labels.append("BB(20,2)")
    if "vwap" in indicators:
        indicator_labels.append("VWAP")
    if "rsi" in indicators:
        indicator_labels.append("RSI(14)")
    if "macd" in indicators:
        indicator_labels.append("MACD(12,26,9)")
    if indicator_labels:
        fig.text(0.06, 0.91, "  •  ".join(indicator_labels), fontsize=8, color="#565a6e", ha="left")

    # Watermark
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fig.text(0.98, 0.01, f"Data: Yahoo Finance  •  {now}", fontsize=7, color="#3d4250", ha="right")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_STYLE["dpi"], bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    logger.info("Chart rendered: %s (%d candles, indicators=%s)", md.symbol, len(df), indicators)
    return buf
