# News-Driven Trading Guide

Complete guide to using the news-driven trading system.

## Overview

The news-driven trading system analyzes news articles from multiple sources using an ensemble of NLP sentiment models to generate trading signals.

### Architecture

```
News Sources (8 total)
       │
       ▼
NewsImpactAnalyzer
  ├── VADER (rule-based)
  ├── TextBlob (pattern-based)
  ├── FinBERT (transformer – financial)
  ├── RoBERTa (transformer – social media)
  └── Keyword Model (financial lexicon)
       │
       ▼
MarketImpact (direction + magnitude + confidence)
       │
       ▼
Trading Signal → Execute / Monitor
```

## Quick Start

```python
from src.news_impact_analyzer import NewsImpactAnalyzer, NewsArticle

analyzer = NewsImpactAnalyzer(use_transformers=False)

article = NewsArticle(
    title="Apple beats Q3 earnings with record iPhone revenue",
    content="Apple Inc. surpassed analyst estimates...",
    source="newsapi",
    symbols=["AAPL"],
)

impact = analyzer.analyze(article)
print(impact.direction)    # "bullish"
print(impact.impact_score) # 0.72
print(impact.confidence)   # 0.85
```

## Sentiment Models

| Model | Type | Best For |
|-------|------|----------|
| VADER | Rule-based | General text, fast |
| TextBlob | Pattern | Short text |
| FinBERT | Transformer | Financial news |
| RoBERTa | Transformer | Social media |
| Keyword | Lexicon | Financial terms |

Enable transformer models (requires GPU):
```python
analyzer = NewsImpactAnalyzer(use_transformers=True)
```

## Interpreting Impact Scores

| Score Range | Direction | Action |
|-------------|-----------|--------|
| > 0.3 | Bullish (high) | Strong buy signal |
| 0.05 to 0.3 | Bullish | Weak buy signal |
| -0.05 to 0.05 | Neutral | Hold / no action |
| -0.3 to -0.05 | Bearish | Weak sell signal |
| < -0.3 | Bearish (high) | Strong sell signal |

## Aggregating Multiple Articles

```python
impacts = analyzer.analyze_batch(articles)
agg = analyzer.aggregate_impact(impacts, symbol="AAPL")

print(agg["direction"])  # "bullish"
print(agg["score"])      # 0.45
print(agg["confidence"]) # 0.72
print(agg["bullish_count"])  # 7
print(agg["bearish_count"])  # 2
```

## Environment Variables

| Variable | Source | Required |
|----------|--------|----------|
| `NEWSAPI_KEY` | NewsAPI | For NewsAPI source |
| `FINNHUB_KEY` | Finnhub | For Finnhub source |
| `POLYGON_KEY` | Polygon | For Polygon source |
| `TWITTER_BEARER_TOKEN` | Twitter | For Twitter source |
| `REDDIT_CLIENT_ID` | Reddit | For OAuth (optional) |
| `REDDIT_CLIENT_SECRET` | Reddit | For OAuth (optional) |
| `CRYPTOPANIC_TOKEN` | CryptoPanic | For CryptoPanic source |

## Running the Example

```bash
python examples/news_driven_trading_example.py
```
