# All News Sources Guide

Complete reference for all 8 news source integrations.

## Source Overview

| # | Source | Class | API Key Required | Free Tier |
|---|--------|-------|-----------------|-----------|
| 1 | NewsAPI | `NewsAPISource` | Yes | ✅ 100 req/day |
| 2 | Finnhub | `FinnhubSource` | Yes | ✅ 60 req/min |
| 3 | Polygon | `PolygonSource` | Yes | ✅ Limited |
| 4 | Twitter/X | `TwitterSource` | Yes | Limited |
| 5 | Reddit | `RedditSource` | Optional | ✅ Public feeds |
| 6 | Seeking Alpha | `SeekingAlphaSource` | No | ✅ RSS |
| 7 | MarketWatch | `MarketWatchSource` | No | ✅ RSS |
| 8 | Crypto News | `CryptoNewsSource` | Optional | ✅ RSS |

## Installation

```bash
pip install requests beautifulsoup4 lxml
```

## 1. NewsAPI

**Sign up:** https://newsapi.org

```python
import os
from src.news_sources import NewsAPISource

src = NewsAPISource(api_key=os.getenv("NEWSAPI_KEY"))
articles = src.fetch(query="AAPL earnings", symbols=["AAPL"])
headlines = src.fetch_top_headlines(category="business")
```

## 2. Finnhub

**Sign up:** https://finnhub.io

```python
from src.news_sources import FinnhubSource

src = FinnhubSource(api_key=os.getenv("FINNHUB_KEY"))
articles = src.fetch_company_news("TSLA", from_date="2024-01-01", to_date="2024-01-31")
market_news = src.fetch_market_news(category="general")
```

## 3. Polygon

**Sign up:** https://polygon.io

```python
from src.news_sources import PolygonSource

src = PolygonSource(api_key=os.getenv("POLYGON_KEY"))
articles = src.fetch_ticker_news("NVDA", max_results=20)
```

## 4. Twitter/X

**Sign up:** https://developer.twitter.com

```python
from src.news_sources import TwitterSource

src = TwitterSource(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))
tweets = src.fetch(query="$AAPL OR #Apple", symbols=["AAPL"])
```

## 5. Reddit

**Sign up (optional):** https://www.reddit.com/prefs/apps

```python
from src.news_sources import RedditSource

# No credentials needed (public feeds)
src = RedditSource(subreddits=["wallstreetbets", "investing"])
posts = src.fetch(query="AAPL", symbols=["AAPL"])

# With OAuth (higher rate limits)
src_auth = RedditSource(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
)
```

## 6. Seeking Alpha

No API key required. Uses public RSS feeds.

```python
from src.news_sources import SeekingAlphaSource

src = SeekingAlphaSource(symbols=["AAPL", "MSFT"])
articles = src.fetch(query="", symbols=["AAPL"])
```

## 7. MarketWatch

No API key required. Uses public RSS feeds.

```python
from src.news_sources import MarketWatchSource

# Available feeds: topstories, marketpulse, realtimeheadlines,
#                  personal_finance, portfolio
src = MarketWatchSource(feed="topstories")
articles = src.fetch(query="earnings")
```

## 8. Crypto News

No key needed for RSS. Optional CryptoPanic token for more results.

**Sign up (optional):** https://cryptopanic.com/developers/api/

```python
from src.news_sources import CryptoNewsSource

src = CryptoNewsSource(cryptopanic_token=os.getenv("CRYPTOPANIC_TOKEN"))
articles = src.fetch(query="bitcoin", symbols=["BTC", "ETH"])
```

## Using All Sources Together

```python
from src.news_sources import (
    NewsAPISource, FinnhubSource, PolygonSource, TwitterSource,
    RedditSource, SeekingAlphaSource, MarketWatchSource, CryptoNewsSource,
)
from src.news_impact_analyzer import NewsImpactAnalyzer

SYMBOLS = ["AAPL", "TSLA"]
QUERY = "AAPL OR Tesla"

sources = [
    NewsAPISource(), FinnhubSource(), PolygonSource(),
    TwitterSource(), RedditSource(), SeekingAlphaSource(symbols=SYMBOLS),
    MarketWatchSource(), CryptoNewsSource(),
]

all_articles = []
for source in sources:
    all_articles.extend(source.fetch(query=QUERY, symbols=SYMBOLS, max_results=10))

analyzer = NewsImpactAnalyzer(use_transformers=False)
impacts = analyzer.analyze_batch(all_articles)
agg = analyzer.aggregate_impact(impacts, symbol="AAPL")
print(agg)
```

## Running the Multi-Source Example

```bash
python examples/multi_source_example.py
```
