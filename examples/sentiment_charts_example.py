"""
Sentiment Charts Example
========================
Shows how to produce all available sentiment visualizations.

Charts are saved to /tmp/ so they can be reviewed without a display.

Run:
    python examples/sentiment_charts_example.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from datetime import datetime, timedelta, timezone

from src import sentiment_charts as sc


def _gen_timestamps(n: int, base: datetime = None):
    base = base or datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [base + timedelta(hours=i * 4) for i in range(n)]


def main():
    out_dir = "/tmp/sentiment_charts"
    os.makedirs(out_dir, exist_ok=True)

    n = 60
    rng = np.random.default_rng(42)
    timestamps = _gen_timestamps(n)
    scores = list(np.clip(rng.normal(0.1, 0.35, n), -1, 1))

    # ------------------------------------------------------------------ #
    # 1. Sentiment over time
    # ------------------------------------------------------------------ #
    print("Generating sentiment over time chart…")
    sc.plot_sentiment_over_time(
        timestamps=timestamps,
        scores=scores,
        symbol="AAPL",
        save_path=os.path.join(out_dir, "sentiment_over_time.png"),
    )

    # ------------------------------------------------------------------ #
    # 2. Sentiment by symbol
    # ------------------------------------------------------------------ #
    print("Generating sentiment by symbol chart…")
    symbol_scores = {
        "AAPL": 0.42,
        "TSLA": -0.25,
        "MSFT": 0.18,
        "AMZN": 0.05,
        "NVDA": 0.67,
        "GOOG": -0.12,
        "META": 0.33,
        "BTC":  -0.08,
    }
    sc.plot_sentiment_by_symbol(
        symbol_scores=symbol_scores,
        save_path=os.path.join(out_dir, "sentiment_by_symbol.png"),
    )

    # ------------------------------------------------------------------ #
    # 3. Sentiment vs price
    # ------------------------------------------------------------------ #
    print("Generating sentiment vs price chart…")
    prices = list(180 + np.cumsum(rng.normal(0, 1.5, n)))
    sc.plot_sentiment_vs_price(
        timestamps=timestamps,
        sentiment_scores=scores,
        prices=prices,
        symbol="AAPL",
        save_path=os.path.join(out_dir, "sentiment_vs_price.png"),
    )

    # ------------------------------------------------------------------ #
    # 4. Sentiment heatmap
    # ------------------------------------------------------------------ #
    print("Generating sentiment heatmap…")
    symbols = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN"]
    dates = [datetime(2024, 1, d) for d in range(1, 8)]
    heatmap_scores = np.clip(rng.normal(0, 0.4, (len(symbols), len(dates))), -1, 1)
    sc.plot_sentiment_heatmap(
        symbols=symbols,
        dates=dates,
        scores=heatmap_scores,
        save_path=os.path.join(out_dir, "sentiment_heatmap.png"),
    )

    # ------------------------------------------------------------------ #
    # 5. Sentiment distribution
    # ------------------------------------------------------------------ #
    print("Generating sentiment distribution chart…")
    sc.plot_sentiment_distribution(
        scores=scores,
        symbol="AAPL",
        save_path=os.path.join(out_dir, "sentiment_distribution.png"),
    )

    # ------------------------------------------------------------------ #
    # 6. Sentiment strength over time
    # ------------------------------------------------------------------ #
    print("Generating sentiment strength over time chart…")
    sc.plot_sentiment_strength_over_time(
        timestamps=timestamps,
        scores=scores,
        window=7,
        symbol="AAPL",
        save_path=os.path.join(out_dir, "sentiment_strength.png"),
    )

    print(f"\n✅ All charts saved to {out_dir}/")


if __name__ == "__main__":
    main()
