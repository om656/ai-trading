"""
Sentiment Charts
================
Comprehensive visualization of sentiment data using matplotlib/seaborn.

Provides:
- Real-time sentiment over time
- Sentiment by symbol
- Sentiment correlation with price
- Sentiment heatmaps
- Historical sentiment trends
- Sentiment distribution charts
"""

import logging
from datetime import datetime
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_PLT_OK = False
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend – safe for servers
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    _PLT_OK = True
except ImportError:
    logger.warning("matplotlib not available – charts will not be rendered.")

_SNS_OK = False
try:
    import seaborn as sns
    _SNS_OK = True
except ImportError:
    pass

_PD_OK = False
try:
    import pandas as pd
    _PD_OK = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_plt(func):
    """Decorator that skips chart functions when matplotlib is unavailable."""
    def wrapper(*args, **kwargs):
        if not _PLT_OK:
            logger.error("matplotlib is required for '%s'.", func.__name__)
            return None
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def _color_for_score(score: float) -> str:
    if score > 0.05:
        return "#2ecc71"   # green
    if score < -0.05:
        return "#e74c3c"   # red
    return "#95a5a6"       # grey


# ---------------------------------------------------------------------------
# Chart functions
# ---------------------------------------------------------------------------

@_require_plt
def plot_sentiment_over_time(
    timestamps: list,
    scores: list,
    symbol: str = "",
    title: str = "",
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Line chart of sentiment compound scores over time.

    Parameters
    ----------
    timestamps : list[datetime]
    scores : list[float]
    symbol : str
    title : str
    save_path : str | None
        File path to save the figure (e.g. "sentiment_over_time.png").
        If None, calls plt.show().

    Returns
    -------
    matplotlib.figure.Figure | None
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    colors = [_color_for_score(s) for s in scores]
    ax.scatter(timestamps, scores, c=colors, s=30, zorder=3)
    ax.plot(timestamps, scores, color="#3498db", linewidth=1.5, alpha=0.7, zorder=2)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.4)

    # Shading
    ax.fill_between(timestamps, scores, 0,
                    where=[s > 0 for s in scores],
                    alpha=0.15, color="#2ecc71", interpolate=True)
    ax.fill_between(timestamps, scores, 0,
                    where=[s <= 0 for s in scores],
                    alpha=0.15, color="#e74c3c", interpolate=True)

    ax.set_xlabel("Time")
    ax.set_ylabel("Sentiment Score")
    ax.set_title(title or f"Sentiment Over Time{' – ' + symbol if symbol else ''}")
    ax.set_ylim(-1.1, 1.1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        logger.info("Saved chart: %s", save_path)
    else:
        plt.show()
    return fig


@_require_plt
def plot_sentiment_by_symbol(
    symbol_scores: dict,
    title: str = "Sentiment by Symbol",
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Horizontal bar chart of average sentiment by symbol.

    Parameters
    ----------
    symbol_scores : dict[str, float]
        Mapping of symbol → average sentiment score.
    title : str
    save_path : str | None

    Returns
    -------
    matplotlib.figure.Figure | None
    """
    symbols = list(symbol_scores.keys())
    scores = [symbol_scores[s] for s in symbols]
    colors = [_color_for_score(s) for s in scores]

    fig, ax = plt.subplots(figsize=(10, max(4, len(symbols) * 0.5)))
    bars = ax.barh(symbols, scores, color=colors, edgecolor="white", height=0.6)
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Average Sentiment Score")
    ax.set_title(title)
    ax.set_xlim(-1.1, 1.1)

    for bar, score in zip(bars, scores):
        ax.text(
            score + (0.02 if score >= 0 else -0.02),
            bar.get_y() + bar.get_height() / 2,
            f"{score:+.3f}",
            va="center",
            ha="left" if score >= 0 else "right",
            fontsize=9,
        )

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    return fig


@_require_plt
def plot_sentiment_vs_price(
    timestamps: list,
    sentiment_scores: list,
    prices: list,
    symbol: str = "",
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Dual-axis chart: sentiment vs price on the same timeline.

    Parameters
    ----------
    timestamps : list[datetime]
    sentiment_scores : list[float]
    prices : list[float]
    symbol : str
    save_path : str | None

    Returns
    -------
    matplotlib.figure.Figure | None
    """
    fig, ax1 = plt.subplots(figsize=(13, 5))
    ax2 = ax1.twinx()

    ax1.plot(timestamps, sentiment_scores, color="#3498db",
             linewidth=1.8, label="Sentiment", alpha=0.85)
    ax1.axhline(0, color="black", linewidth=0.6, linestyle="--", alpha=0.3)
    ax1.set_ylabel("Sentiment Score", color="#3498db")
    ax1.set_ylim(-1.1, 1.1)
    ax1.tick_params(axis="y", labelcolor="#3498db")

    ax2.plot(timestamps, prices, color="#e67e22",
             linewidth=1.8, label="Price", alpha=0.85)
    ax2.set_ylabel("Price ($)", color="#e67e22")
    ax2.tick_params(axis="y", labelcolor="#e67e22")

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    plt.xticks(rotation=45)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    ax1.set_title(f"Sentiment vs Price{' – ' + symbol if symbol else ''}")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    return fig


@_require_plt
def plot_sentiment_heatmap(
    symbols: list,
    dates: list,
    scores: "np.ndarray",
    title: str = "Sentiment Heatmap",
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Heatmap of sentiment scores (symbols × dates).

    Parameters
    ----------
    symbols : list[str]
    dates : list[str | datetime]
    scores : np.ndarray
        Shape (len(symbols), len(dates)).
    title : str
    save_path : str | None

    Returns
    -------
    matplotlib.figure.Figure | None
    """
    fig, ax = plt.subplots(figsize=(max(8, len(dates) * 0.6), max(4, len(symbols) * 0.5)))

    date_labels = [
        d.strftime("%m/%d") if isinstance(d, datetime) else str(d)
        for d in dates
    ]

    if _SNS_OK:
        sns.heatmap(
            scores,
            xticklabels=date_labels,
            yticklabels=symbols,
            cmap="RdYlGn",
            vmin=-1,
            vmax=1,
            center=0,
            annot=True,
            fmt=".2f",
            linewidths=0.5,
            ax=ax,
        )
    else:
        im = ax.imshow(scores, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(date_labels)))
        ax.set_xticklabels(date_labels, rotation=45, ha="right")
        ax.set_yticks(range(len(symbols)))
        ax.set_yticklabels(symbols)
        plt.colorbar(im, ax=ax, label="Sentiment")

    ax.set_title(title)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    return fig


@_require_plt
def plot_sentiment_distribution(
    scores: list,
    symbol: str = "",
    bins: int = 30,
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Histogram of sentiment score distribution.

    Parameters
    ----------
    scores : list[float]
    symbol : str
    bins : int
    save_path : str | None

    Returns
    -------
    matplotlib.figure.Figure | None
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    if _SNS_OK:
        sns.histplot(scores, bins=bins, kde=True, ax=ax,
                     color="#3498db", edgecolor="white")
    else:
        ax.hist(scores, bins=bins, color="#3498db", edgecolor="white")

    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    mean_score = float(np.mean(scores)) if scores else 0.0
    ax.axvline(mean_score, color="#e74c3c", linestyle="--",
               linewidth=1.5, label=f"Mean: {mean_score:+.3f}")
    ax.legend()
    ax.set_xlabel("Sentiment Score")
    ax.set_ylabel("Frequency")
    ax.set_title(f"Sentiment Distribution{' – ' + symbol if symbol else ''}")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    return fig


@_require_plt
def plot_sentiment_strength_over_time(
    timestamps: list,
    scores: list,
    window: int = 5,
    symbol: str = "",
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Plot rolling mean and confidence bands of sentiment over time.

    Parameters
    ----------
    timestamps : list[datetime]
    scores : list[float]
    window : int
        Rolling window size.
    symbol : str
    save_path : str | None

    Returns
    -------
    matplotlib.figure.Figure | None
    """
    arr = np.array(scores, dtype=float)
    rolling_mean: list = []
    rolling_std: list = []
    for i in range(len(arr)):
        start = max(0, i - window + 1)
        chunk = arr[start : i + 1]
        rolling_mean.append(float(chunk.mean()))
        rolling_std.append(float(chunk.std()))

    rm = np.array(rolling_mean)
    rs = np.array(rolling_std)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(timestamps, rm, color="#3498db", linewidth=2, label="Rolling Mean")
    ax.fill_between(timestamps, rm - rs, rm + rs,
                    alpha=0.25, color="#3498db", label="±1 Std Dev")
    ax.scatter(timestamps, scores, color="#95a5a6", s=15, alpha=0.5, zorder=3)
    ax.axhline(0, color="black", linewidth=0.7, linestyle="--", alpha=0.4)
    ax.set_xlabel("Time")
    ax.set_ylabel("Sentiment Score")
    ax.set_title(
        f"Sentiment Strength Over Time (window={window})"
        f"{' – ' + symbol if symbol else ''}"
    )
    ax.set_ylim(-1.1, 1.1)
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
    else:
        plt.show()
    return fig
