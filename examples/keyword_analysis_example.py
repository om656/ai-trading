"""
Keyword Analysis Example
========================
Shows how to discover which keywords predict profitable trades.

Run:
    python examples/keyword_analysis_example.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from src.news_impact_analyzer import NewsImpactAnalyzer, NewsArticle
from src.keyword_analyzer import KeywordAnalyzer


SAMPLE_ARTICLES = [
    ("Apple beats earnings, raises guidance, record profit", 0.65),
    ("Tesla misses delivery targets, shares fall", -0.45),
    ("NVIDIA revenue surges on AI chip demand", 0.75),
    ("Fed signals rate cut possible in September", 0.20),
    ("Startup raises $500M Series C funding round", 0.30),
    ("Company announces major layoff, restructuring", -0.50),
    ("Drug approved by FDA, biotech soars", 0.80),
    ("Lawsuit filed against tech giant for antitrust", -0.35),
    ("Dividend increase announced, buyback program launched", 0.40),
    ("Bankruptcy filing shocks investors", -0.90),
    ("Partnership deal signed, revenue expected to grow", 0.55),
    ("CEO resigns amid scandal, stock drops", -0.60),
    ("New product launch exceeds expectations", 0.45),
    ("Quarterly guidance cut, outlook weak", -0.40),
    ("Record quarterly profit reported, beat estimates", 0.70),
]


def main():
    print("=" * 60)
    print("KEYWORD ANALYSIS DEMO")
    print("=" * 60)

    analyzer = NewsImpactAnalyzer(use_transformers=False)

    # Build articles and analyze them
    articles = []
    for title, _ in SAMPLE_ARTICLES:
        articles.append(NewsArticle(
            title=title,
            content=title,   # simple demo – content same as title
            source="example",
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ))
    impacts = analyzer.analyze_batch(articles)

    # Run keyword analysis
    kw_analyzer = KeywordAnalyzer(min_occurrences=1, top_n=10)
    report = kw_analyzer.analyze(impacts)

    print("\n📈 TOP BULLISH KEYWORDS")
    print("-" * 40)
    for word, avg_score, count in report.top_bullish_keywords:
        print(f"  {word:<20s} avg={avg_score:+.4f}  count={count}")

    print("\n📉 TOP BEARISH KEYWORDS")
    print("-" * 40)
    for word, avg_score, count in report.top_bearish_keywords:
        print(f"  {word:<20s} avg={avg_score:+.4f}  count={count}")

    print("\n📊 MOST FREQUENT KEYWORDS")
    print("-" * 40)
    for word, count in report.most_frequent_keywords[:10]:
        score = report.keyword_impact_map.get(word, {}).get("avg_score", 0)
        print(f"  {word:<20s} count={count}  avg_score={score:+.4f}")

    print(f"\nSummary:\n{report.summary}")

    # Cluster by a specific keyword
    print("\n" + "=" * 60)
    cluster = kw_analyzer.cluster_by_keyword(impacts, "earnings")
    print(f"Keyword 'earnings': {len(cluster['articles'])} articles, "
          f"avg_impact={cluster['avg_impact']:+.4f}, "
          f"win_rate={cluster['win_rate']:.1f}%")


if __name__ == "__main__":
    main()
