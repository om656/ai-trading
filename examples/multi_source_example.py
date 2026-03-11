"""
Multi-Source News Example
=========================
Demonstrates fetching news from all 8 configured sources and combining
the results into a single unified analysis.

NOTE: Most sources require API keys set as environment variables.
      Sources without valid keys are skipped gracefully.

Run:
    python examples/multi_source_example.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.news_impact_analyzer import NewsImpactAnalyzer
from src.news_sources import (
    NewsAPISource,
    FinnhubSource,
    PolygonSource,
    TwitterSource,
    RedditSource,
    SeekingAlphaSource,
    MarketWatchSource,
    CryptoNewsSource,
)
from src.event_detector import EventDetector

SYMBOLS = ["AAPL", "TSLA", "NVDA"]
QUERY = "AAPL OR Tesla OR NVIDIA"


def fetch_all(symbols: list, query: str, max_per_source: int = 5) -> list:
    sources = [
        ("NewsAPI",       NewsAPISource()),
        ("Finnhub",       FinnhubSource()),
        ("Polygon",       PolygonSource()),
        ("Twitter/X",     TwitterSource()),
        ("Reddit",        RedditSource()),
        ("SeekingAlpha",  SeekingAlphaSource(symbols=symbols)),
        ("MarketWatch",   MarketWatchSource()),
        ("CryptoNews",    CryptoNewsSource()),
    ]

    all_articles = []
    print(f"{'Source':<18} {'Articles':>8}")
    print("-" * 30)
    for name, source in sources:
        try:
            articles = source.fetch(query=query, symbols=symbols,
                                    max_results=max_per_source)
            count = len(articles)
            print(f"{name:<18} {count:>8}")
            all_articles.extend(articles)
        except Exception as exc:
            print(f"{name:<18} {'ERROR':>8}  ({exc})")
    print("-" * 30)
    print(f"{'TOTAL':<18} {len(all_articles):>8}\n")
    return all_articles


def main():
    print("=" * 60)
    print("MULTI-SOURCE NEWS ANALYSIS")
    print("=" * 60)

    articles = fetch_all(SYMBOLS, QUERY)

    if not articles:
        print("No articles fetched (likely missing API keys). Using demo data…")
        from datetime import datetime, timezone
        from src.news_impact_analyzer import NewsArticle
        articles = [
            NewsArticle(
                title="Apple partners with OpenAI to bring AI features to iPhone",
                content="Apple and OpenAI announced a strategic partnership.",
                source="demo",
                symbols=["AAPL"],
                published_at=datetime(2024, 6, 10, 18, 0, tzinfo=timezone.utc),
            ),
            NewsArticle(
                title="Tesla Autopilot recall affects 2 million vehicles",
                content="NHTSA ordered Tesla to recall vehicles due to Autopilot concerns.",
                source="demo",
                symbols=["TSLA"],
                published_at=datetime(2024, 6, 9, 12, 0, tzinfo=timezone.utc),
            ),
        ]

    # Analyze
    analyzer = NewsImpactAnalyzer(use_transformers=False, symbols=SYMBOLS)
    impacts = analyzer.analyze_batch(articles)

    # Per-symbol aggregate
    print("SYMBOL SIGNALS")
    print("=" * 60)
    for sym in SYMBOLS:
        agg = analyzer.aggregate_impact(impacts, symbol=sym)
        if agg["articles_analyzed"] == 0:
            continue
        print(
            f"{sym:6s} | {agg['direction']:7s} | "
            f"score={agg['score']:+.4f} | "
            f"conf={agg['confidence']:.4f} | "
            f"📰 {agg['articles_analyzed']} articles "
            f"(🟢 {agg['bullish_count']} / 🔴 {agg['bearish_count']} / ⚪ {agg['neutral_count']})"
        )

    # Event detection
    print("\nDETECTED MARKET EVENTS")
    print("=" * 60)
    detector = EventDetector(min_confidence=0.1)
    events = detector.detect([i.article for i in impacts])
    if events:
        for event in events:
            print(event)
    else:
        print("No significant events detected.")

    summary = detector.summarize(events)
    if summary:
        print(f"\nEvent summary: {summary}")


if __name__ == "__main__":
    main()
