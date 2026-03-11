"""
NewsAPI Source
==============
Fetches news articles from newsapi.org.

Requires: NEWSAPI_KEY environment variable (free tier: 100 req/day).
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

# Lazy import from parent package to avoid circular dependencies
def _make_article(title, content, source, url="", published_at=None, symbols=None):
    from src.news_impact_analyzer import NewsArticle
    return NewsArticle(
        title=title, content=content, source=source,
        url=url, published_at=published_at, symbols=symbols or [],
    )


class NewsAPISource:
    """
    Wrapper around the NewsAPI.org REST API.

    Parameters
    ----------
    api_key : str | None
        API key. Falls back to NEWSAPI_KEY env variable.
    """

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWSAPI_KEY", "")
        self.name = "newsapi"

    def fetch(self, query: str, symbols: Optional[list] = None,
              max_results: int = 20) -> list:
        """
        Fetch recent news articles matching *query*.

        Parameters
        ----------
        query : str
            Search terms (e.g. "AAPL earnings").
        symbols : list[str] | None
            Ticker symbols to tag on returned articles.
        max_results : int
            Maximum number of articles to return.

        Returns
        -------
        list[NewsArticle]
        """
        if not self.api_key:
            logger.warning("NewsAPISource: no API key configured.")
            return []
        if not _REQUESTS_OK:
            logger.warning("NewsAPISource: 'requests' library not installed.")
            return []

        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(max_results, 100),
            "apiKey": self.api_key,
        }
        try:
            resp = requests.get(f"{self.BASE_URL}/everything", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("NewsAPISource fetch error: %s", exc)
            return []

        articles = []
        for item in data.get("articles", []):
            pub = None
            if item.get("publishedAt"):
                try:
                    pub = datetime.fromisoformat(
                        item["publishedAt"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            articles.append(_make_article(
                title=item.get("title") or "",
                content=item.get("description") or item.get("content") or "",
                source=f"{self.name}/{item.get('source', {}).get('name', '')}",
                url=item.get("url", ""),
                published_at=pub,
                symbols=list(symbols or []),
            ))
        return articles[:max_results]

    def fetch_top_headlines(self, category: str = "business",
                            max_results: int = 20) -> list:
        """Fetch top headlines for a given category."""
        if not self.api_key or not _REQUESTS_OK:
            return []
        params = {
            "category": category,
            "language": "en",
            "pageSize": min(max_results, 100),
            "apiKey": self.api_key,
        }
        try:
            resp = requests.get(f"{self.BASE_URL}/top-headlines", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("NewsAPISource top-headlines error: %s", exc)
            return []
        articles = []
        for item in data.get("articles", []):
            articles.append(_make_article(
                title=item.get("title") or "",
                content=item.get("description") or "",
                source=f"{self.name}/{item.get('source', {}).get('name', '')}",
                url=item.get("url", ""),
            ))
        return articles[:max_results]
