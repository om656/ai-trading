"""
Backtesting Example
===================
Demonstrates how to run a historical news-driven backtest.

Run:
    python examples/backtesting_example.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from src.news_impact_analyzer import NewsArticle
from src.news_backtester import NewsBacktester


def _build_sample_articles() -> list:
    """Create a small set of dated articles for demonstration."""
    return [
        NewsArticle(
            title="AAPL beats earnings, raises guidance",
            content="Apple reported record quarterly profits exceeding analyst expectations.",
            source="example",
            symbols=["AAPL"],
            published_at=datetime(2023, 8, 4, 20, 0, tzinfo=timezone.utc),
        ),
        NewsArticle(
            title="AAPL faces antitrust lawsuit from DOJ",
            content="The Department of Justice filed an antitrust lawsuit against Apple.",
            source="example",
            symbols=["AAPL"],
            published_at=datetime(2023, 9, 12, 14, 0, tzinfo=timezone.utc),
        ),
        NewsArticle(
            title="AAPL unveils new iPhone 15 lineup",
            content="Apple unveiled the iPhone 15 series at its annual September event.",
            source="example",
            symbols=["AAPL"],
            published_at=datetime(2023, 9, 13, 17, 0, tzinfo=timezone.utc),
        ),
        NewsArticle(
            title="Fed signals no rate hike – markets surge",
            content="The Federal Reserve held rates steady, boosting tech stocks.",
            source="example",
            symbols=["AAPL", "QQQ"],
            published_at=datetime(2023, 11, 2, 19, 0, tzinfo=timezone.utc),
        ),
        NewsArticle(
            title="AAPL Q4 earnings miss on services revenue",
            content="Apple's Q4 results came in below estimates, services growth slowed.",
            source="example",
            symbols=["AAPL"],
            published_at=datetime(2023, 11, 3, 21, 0, tzinfo=timezone.utc),
        ),
    ]


def main():
    articles = _build_sample_articles()

    print("=" * 60)
    print("NEWS-DRIVEN BACKTEST – AAPL (2023)")
    print("=" * 60)

    backtester = NewsBacktester(
        symbol="AAPL",
        initial_capital=10_000.0,
        position_size_pct=0.10,
        sentiment_threshold=0.2,
        hold_hours=24,
    )

    result = backtester.run(
        articles=articles,
        start_date="2023-08-01",
        end_date="2023-12-01",
    )

    print(backtester.generate_report(result))

    print("\nEquity curve (last 10 data points):")
    for i, val in enumerate(result.equity_curve[-10:]):
        print(f"  [{i:2d}] ${val:,.2f}")


if __name__ == "__main__":
    main()
