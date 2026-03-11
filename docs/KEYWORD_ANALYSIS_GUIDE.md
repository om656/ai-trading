# Keyword Analysis Guide

Guide to identifying the most profitable keywords in news articles.

## Overview

The `KeywordAnalyzer` processes `MarketImpact` objects to discover which
words in headlines and article bodies correlate most strongly with profitable
trading signals.

## Quick Start

```python
from src.news_impact_analyzer import NewsImpactAnalyzer, NewsArticle
from src.keyword_analyzer import KeywordAnalyzer

# Analyze articles
analyzer = NewsImpactAnalyzer(use_transformers=False)
impacts = analyzer.analyze_batch(articles)

# Run keyword analysis
kw_analyzer = KeywordAnalyzer(min_occurrences=2, top_n=20)
report = kw_analyzer.analyze(impacts)

print("Top bullish keywords:")
for word, avg_score, count in report.top_bullish_keywords:
    print(f"  {word}: avg_score={avg_score:+.4f}, count={count}")

print("Top bearish keywords:")
for word, avg_score, count in report.top_bearish_keywords:
    print(f"  {word}: avg_score={avg_score:+.4f}, count={count}")
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_word_length` | `4` | Minimum characters in a keyword |
| `min_occurrences` | `2` | Minimum times word must appear |
| `top_n` | `20` | Number of keywords to return |

## KeywordReport Fields

| Field | Type | Description |
|-------|------|-------------|
| `top_bullish_keywords` | `list[(word, score, count)]` | Words with highest avg positive impact |
| `top_bearish_keywords` | `list[(word, score, count)]` | Words with highest avg negative impact |
| `most_frequent_keywords` | `list[(word, count)]` | Most common financial words |
| `keyword_impact_map` | `dict` | Full impact data for each word |
| `total_articles` | `int` | Number of articles analyzed |
| `summary` | `str` | Human-readable summary |

## Clustering by Keyword

Find all articles containing a specific word and their statistics:

```python
result = kw_analyzer.cluster_by_keyword(impacts, "earnings")
print(f"Articles: {len(result['articles'])}")
print(f"Avg Impact: {result['avg_impact']:+.4f}")
print(f"Win Rate: {result['win_rate']:.1f}%")
```

## Example Output

```
Top bullish keywords:
  earnings    avg_score=+0.6234, count=45
  profit      avg_score=+0.5891, count=38
  approval    avg_score=+0.7123, count=12
  dividend    avg_score=+0.4567, count=23
  surge       avg_score=+0.5432, count=31

Top bearish keywords:
  bankruptcy  avg_score=-0.8901, count=8
  lawsuit     avg_score=-0.4567, count=19
  recall      avg_score=-0.5234, count=11
  fraud       avg_score=-0.6789, count=7
  layoff      avg_score=-0.4123, count=14
```

## Running the Example

```bash
python examples/keyword_analysis_example.py
```
