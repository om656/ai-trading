"""
News Sources Package
====================
Integrations with 8 external news and social-media data sources.
"""

from .newsapi_source import NewsAPISource
from .finnhub_source import FinnhubSource
from .polygon_source import PolygonSource
from .twitter_source import TwitterSource
from .reddit_source import RedditSource
from .seeking_alpha_source import SeekingAlphaSource
from .marketwatch_source import MarketWatchSource
from .crypto_news_source import CryptoNewsSource

__all__ = [
    "NewsAPISource",
    "FinnhubSource",
    "PolygonSource",
    "TwitterSource",
    "RedditSource",
    "SeekingAlphaSource",
    "MarketWatchSource",
    "CryptoNewsSource",
]
