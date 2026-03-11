"""News fetcher with multi-source RSS support."""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class NewsAPI:
    """Fetches news from NewsAPI and RSS feeds."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/"

    def get_top_headlines(self, country: str = "us", category: str = "business") -> dict:
        """Fetch top headlines from NewsAPI."""
        if not self.api_key:
            logger.warning("No NewsAPI key configured")
            return {"articles": []}
        try:
            url = f"{self.base_url}top-headlines"
            params = {"country": country, "category": category, "apiKey": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Error fetching headlines: %s", e)
            return {"articles": []}

    def search_news(self, query: str, page_size: int = 10) -> dict:
        """Search for news articles by keyword."""
        if not self.api_key:
            return {"articles": []}
        try:
            url = f"{self.base_url}everything"
            params = {"q": query, "pageSize": page_size, "sortBy": "publishedAt", "apiKey": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Error searching news: %s", e)
            return {"articles": []}

    def get_symbol_news(self, symbol: str) -> list:
        """Get news headlines for a specific stock symbol."""
        result = self.search_news(symbol)
        articles = result.get("articles", [])
        return [a.get("title", "") for a in articles if a.get("title")]

    def get_rss_headlines(self, symbol: str = "") -> list:
        """Fetch headlines from RSS feeds (no API key needed)."""
        headlines = []
        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser not installed; RSS feeds unavailable")
            return headlines

        from src.config import Config
        for feed_url in Config.NEWS_SOURCES:
            try:
                url = feed_url.format(symbol=symbol) if "{symbol}" in feed_url else feed_url
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    headlines.append(entry.get("title", ""))
            except Exception as e:
                logger.debug("RSS feed error for %s: %s", feed_url, e)

        return [h for h in headlines if h]
