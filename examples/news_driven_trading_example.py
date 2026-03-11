"""
News-Driven Trading Example
============================
Demonstrates end-to-end news analysis → trading signal generation.

Run:
    python examples/news_driven_trading_example.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from src.news_impact_analyzer import NewsImpactAnalyzer, NewsArticle


def main():
    # ------------------------------------------------------------------ #
    # 1. Build sample articles (replace with live source in production)
    # ------------------------------------------------------------------ #
    articles = [
        NewsArticle(
            title="Apple beats Q3 earnings estimates with record iPhone revenue",
            content=(
                "Apple Inc. reported quarterly earnings that surpassed analyst expectations, "
                "driven by strong iPhone sales and growing services revenue. "
                "EPS came in at $1.52 vs the expected $1.39."
            ),
            source="newsapi/example",
            symbols=["AAPL"],
            published_at=datetime(2024, 8, 2, 21, 0, tzinfo=timezone.utc),
        ),
        NewsArticle(
            title="Tesla misses delivery targets, shares fall pre-market",
            content=(
                "Tesla delivered fewer vehicles than analysts expected in Q2, "
                "causing shares to drop 6% in after-hours trading. "
                "Production issues at the Berlin Gigafactory were cited as a key factor."
            ),
            source="finnhub/example",
            symbols=["TSLA"],
            published_at=datetime(2024, 7, 3, 6, 0, tzinfo=timezone.utc),
        ),
        NewsArticle(
            title="Federal Reserve signals possible rate cut in September",
            content=(
                "Fed Chair Powell hinted at a potential interest rate reduction at the "
                "September FOMC meeting, citing easing inflation and stable employment data."
            ),
            source="marketwatch/example",
            symbols=["SPY", "QQQ"],
            published_at=datetime(2024, 7, 31, 18, 0, tzinfo=timezone.utc),
        ),
    ]

    # ------------------------------------------------------------------ #
    # 2. Analyze articles
    # ------------------------------------------------------------------ #
    print("Initializing NewsImpactAnalyzer (lightweight models)…")
    analyzer = NewsImpactAnalyzer(use_transformers=False)

    print(f"\nAnalyzing {len(articles)} articles…\n" + "=" * 60)
    impacts = analyzer.analyze_batch(articles)

    for impact in impacts:
        print(f"Title   : {impact.article.title}")
        print(f"Source  : {impact.article.source}")
        print(f"Symbols : {impact.affected_symbols}")
        print(f"Sentiment compound : {impact.sentiment.compound:+.4f}")
        print(f"Impact score       : {impact.impact_score:+.4f}")
        print(f"Direction          : {impact.direction.upper()}")
        print(f"Magnitude          : {impact.magnitude}")
        print(f"Confidence         : {impact.confidence:.4f}")
        print(f"Keywords detected  : {impact.keywords}")
        print("-" * 60)

    # ------------------------------------------------------------------ #
    # 3. Aggregate signal per symbol
    # ------------------------------------------------------------------ #
    print("\nAGGREGATED SIGNALS")
    print("=" * 60)
    for sym in ["AAPL", "TSLA", "SPY"]:
        agg = analyzer.aggregate_impact(impacts, symbol=sym)
        print(
            f"{sym:6s} | direction={agg['direction']:7s} | "
            f"score={agg['score']:+.4f} | "
            f"conf={agg['confidence']:.4f} | "
            f"articles={agg['articles_analyzed']}"
        )


if __name__ == "__main__":
    main()
